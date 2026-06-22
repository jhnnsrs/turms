"""The ``input_funcs`` plugin.

Generates a small factory function for every GraphQL input type that builds and
returns the corresponding pydantic input model. Modeled on the ``funcs`` plugin,
but instead of building a ``variables`` dict and calling an executor it constructs
the model directly (``return SomeInput(**data)``).

Scalar parameters can be made *coercible* through ``coercible_scalars`` (same
mechanism as the ``funcs`` plugin), so callers may pass friendlier types
(e.g. ``ID -> pydantic.UUID4``); the input model / pydantic performs the coercion.
"""

import ast
from typing import Dict, List

from graphql import GraphQLInputObjectType, GraphQLNonNull, GraphQLSchema
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from turms.config import GeneratorConfig, PythonType
from turms.plugins.base import Plugin, PluginConfig
from turms.plugins.funcs import (
    dict_str_any_annotation,
    generate_input_type_descriptions,
    generate_input_type_params,
)
from turms.referencer import create_reference_registry_from_documents
from turms.registry import ClassRegistry
from turms.utils import parse_documents


class InputFuncsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(
        extra="forbid", env_prefix="TURMS_PLUGINS_INPUTFUNCS_"
    )
    type: str = "turms.plugins.input_funcs.InputFuncsPlugin"
    coercible_scalars: Dict[str, PythonType] = {}
    """Map of scalar names to a coercible python type used in the factory params."""
    skip_underscore: bool = True
    skip_unreferenced: bool = True
    prepend: str = ""
    """Optional prefix for the generated factory function name."""
    extract_documentation: bool = True


def generate_input_func(
    typename: str,
    input_type: GraphQLInputObjectType,
    config: GeneratorConfig,
    plugin_config: InputFuncsPluginConfig,
    registry: ClassRegistry,
) -> ast.FunctionDef:
    """Builds a factory function that constructs and returns the input model."""
    class_name = registry.get_inputtype_class(typename)

    func_name = plugin_config.prepend + registry.generate_parameter_name(typename)
    if func_name == class_name:
        # Avoid shadowing the model class (would make the body call itself).
        func_name += "_"

    # Required fields -> positional params; optional fields -> keyword params
    # defaulting to UNSET (so they can be omitted). Honors coercible_scalars.
    pos_args, kw_args, kw_values = generate_input_type_params(
        input_type, plugin_config, registry
    )

    body: List[ast.stmt] = []

    if plugin_config.extract_documentation:
        doc = f"Creates a {class_name}\n\nArguments:\n" + (
            generate_input_type_descriptions(input_type, registry)
        )
        body.append(ast.Expr(value=ast.Constant(value=doc)))

    # data: Dict[str, Any] = {}
    body.append(
        ast.AnnAssign(
            target=ast.Name(id="data", ctx=ast.Store()),
            annotation=dict_str_any_annotation(registry),
            value=ast.Dict(keys=[], values=[]),
            simple=1,
        )
    )

    for value_key, value in input_type.fields.items():
        field_param = registry.generate_node_name(value_key)
        # Key by the GraphQL field name (the model's alias) so construction works
        # regardless of populate_by_name.
        subscript = ast.Subscript(
            value=ast.Name(id="data", ctx=ast.Load()),
            slice=ast.Constant(value=value_key),
            ctx=ast.Store(),
        )
        param_value = ast.Name(id=field_param, ctx=ast.Load())

        if isinstance(value.type, GraphQLNonNull):
            # required -> always present
            body.append(ast.Assign(targets=[subscript], value=param_value))
        else:
            # optional -> only set when the caller provided it (not UNSET)
            body.append(
                ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=field_param, ctx=ast.Load()),
                        ops=[ast.IsNot()],
                        comparators=[registry.reference_unset()],
                    ),
                    body=[
                        ast.Assign(
                            targets=[subscript],
                            value=ast.Name(id=field_param, ctx=ast.Load()),
                        )
                    ],
                    orelse=[],
                )
            )

    # return ClassName(**data)
    body.append(
        ast.Return(
            value=ast.Call(
                func=ast.Name(id=class_name, ctx=ast.Load()),
                args=[],
                keywords=[
                    ast.keyword(arg=None, value=ast.Name(id="data", ctx=ast.Load()))
                ],
            )
        )
    )

    return ast.FunctionDef(
        name=func_name,
        args=ast.arguments(
            args=pos_args + kw_args,
            posonlyargs=[],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=kw_values,
        ),
        body=body,
        decorator_list=[],
        returns=ast.Name(id=class_name, ctx=ast.Load()),
    )


def generate_input_funcs(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: InputFuncsPluginConfig,
    registry: ClassRegistry,
) -> List[ast.AST]:
    tree: List[ast.AST] = []

    inputobjects_type = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLInputObjectType)
    }

    if plugin_config.skip_unreferenced and config.documents:
        ref_registry = create_reference_registry_from_documents(
            client_schema, parse_documents(client_schema, config.documents, config)
        )
    else:
        ref_registry = None

    for key, type in inputobjects_type.items():
        if ref_registry and key not in ref_registry.inputs:
            continue

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        # The factory needs the model class generated by the InputsPlugin; skip
        # input types that were not generated (e.g. a different skip config).
        if key not in registry.inputtype_class_map:
            continue

        tree.append(
            generate_input_func(key, type, config, plugin_config, registry)
        )

    return tree


class InputFuncsPlugin(Plugin):
    """Generates a factory function per input type that constructs the model.

    Must run AFTER the ``InputsPlugin`` (and ``EnumsPlugin``) so the referenced
    model / enum classes already exist.
    """

    config: InputFuncsPluginConfig = Field(default_factory=InputFuncsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        # Merge the global coercible_scalars with this plugin's overrides (plugin
        # entries win) so funcs and input_funcs can share a global config.
        plugin_config = self.config.model_copy(
            update={
                "coercible_scalars": {
                    **config.coercible_scalars,
                    **self.config.coercible_scalars,
                }
            }
        )
        return generate_input_funcs(client_schema, config, plugin_config, registry)
