from graphql import (
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
)
from pydantic_settings import SettingsConfigDict
from turms.plugins.base import Plugin, PluginConfig
import ast
from typing import List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import Field
from graphql.type.definition import (
    GraphQLEnumType,
)
from turms.referencer import create_reference_registry_from_documents
from turms.registry import ClassRegistry
from turms.utils import (
    generate_pydantic_config,
    get_additional_bases_for_type,
    parse_documents,
)
from turms.config import GraphQLTypes


class InputsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(extra="forbid", env_prefix="TURMS_PLUGINS_INPUTS_")
    type: str = "turms.plugins.inputs.InputsPlugin"
    inputtype_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = True
    skip_unreferenced: bool = True


def generate_input_annotation(
    type: GraphQLInputType,
    parent: str,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
    is_optional=True,
):
    if isinstance(type, GraphQLScalarType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(type.name),
            )

        return registry.reference_scalar(type.name)

    if isinstance(type, GraphQLInputObjectType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_inputtype(type.name, parent),
                ctx=ast.Load(),
            )
        return registry.reference_inputtype(type.name, parent)

    if isinstance(type, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_enum(
                    type.name, parent, allow_forward=not config.force_plugin_order
                ),
                ctx=ast.Load(),
            )
        return registry.reference_enum(
            type.name, parent, allow_forward=not config.force_plugin_order
        )

    if isinstance(type, GraphQLNonNull):
        return generate_input_annotation(
            type.of_type, parent, config, plugin_config, registry, is_optional=False
        )

    if isinstance(type, GraphQLList):
        if (
            config.freeze.enabled
            and GraphQLTypes.INPUT in config.freeze.types
            and config.freeze.convert_list_to_tuple
        ):
            registry.register_import("typing.Tuple")

            def list_builder(x):
                return ast.Subscript(
                    value=ast.Name("Tuple", ctx=ast.Load()),
                    slice=ast.Tuple(elts=[x,  ast.Constant(value=...)], ctx=ast.Load()),
                    ctx=ast.Load(),
                )

        else:
            registry.register_import("typing.List")

            def list_builder(x):
                return ast.Subscript(
                    value=ast.Name("List", ctx=ast.Load()), slice=x, ctx=ast.Load()
                )

        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=list_builder(
                    generate_input_annotation(
                        type.of_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    )
                ),
                ctx=ast.Load(),
            )

        return list_builder(
            generate_input_annotation(
                type.of_type, parent, config, plugin_config, registry, is_optional=True
            )
        )

    raise NotImplementedError(f"Unknown input type {type}")


def generate_inputs(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
):
    tree = []

    inputobjects_type = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLInputObjectType)
    }

    if plugin_config.skip_unreferenced and config.documents:
        ref_registry = create_reference_registry_from_documents(
            client_schema, parse_documents(client_schema, config.documents)
        )
    else:
        ref_registry = None

    for base in plugin_config.inputtype_bases:
        registry.register_import(base)

    for key, type in inputobjects_type.items():
        if ref_registry and key not in ref_registry.inputs:
            continue

        if plugin_config.skip_underscore and key.startswith("_"):  # pragma: no cover
            continue

        additional_bases = get_additional_bases_for_type(type.name, config, registry)
        name = registry.generate_inputtype(key)
        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

        for value_key, value in type.fields.items():
            field_name = registry.generate_node_name(value_key)

            if field_name != value_key:
                registry.register_import("pydantic.Field")
                keywords = [
                    ast.keyword(arg="alias", value=ast.Constant(value=value_key))
                ]
                if not isinstance(value.type, GraphQLNonNull):
                    keywords.append(
                        ast.keyword(arg="default", value=ast.Constant(None))
                    )

                assign = ast.AnnAssign(
                    target=ast.Name(field_name, ctx=ast.Store()),
                    annotation=generate_input_annotation(
                        value.type,
                        name,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    ),
                    value=ast.Call(
                        func=ast.Name(id="Field", ctx=ast.Load()),
                        args=[],
                        keywords=keywords,
                    ),
                    simple=1,
                )

            else:
                assign = ast.AnnAssign(
                    target=ast.Name(value_key, ctx=ast.Store()),
                    annotation=generate_input_annotation(
                        value.type,
                        name,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    ),
                    simple=1,
                    value=(
                        ast.Constant(None)
                        if not isinstance(value.type, GraphQLNonNull)
                        else None
                    ),
                )

            potential_comment = (
                value.description
                if not value.deprecation_reason
                else f"DEPRECATED: {value.description}"
            )

            if potential_comment:
                fields += [
                    assign,
                    ast.Expr(value=ast.Constant(value=potential_comment)),
                ]

            else:
                fields += [assign]

        tree.append(
            ast.ClassDef(
                name,
                bases=additional_bases
                + [
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.inputtype_bases
                ],
                decorator_list=[],
                keywords=[],
                body=fields
                + generate_pydantic_config(GraphQLTypes.INPUT, config, registry, typename=key),
            )
        )

    return tree


class InputsPlugin(Plugin):
    """Generate pydantic Models for GraphQL inputs

    This plugin generates pydantic models for all GraphQL inputtypes in
    your schema. It will generate a model for each inputtype in your schema.

    """

    config: InputsPluginConfig = Field(default_factory=InputsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        for base in self.config.inputtype_bases:
            registry.register_import(base)

        return generate_inputs(client_schema, config, self.config, registry)
