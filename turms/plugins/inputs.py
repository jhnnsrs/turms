from graphql import (
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
)
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
from turms.registry import ClassRegistry
from turms.utils import generate_config_class, get_additional_bases_for_type


class InputsPluginConfig(PluginConfig):
    type = "turms.plugins.inputs.InputsPlugin"
    inputtype_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_INPUTS_"


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
        if is_optional:
            registry.register_import("typing.Optional")
            registry.register_import("typing.List")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("List", ctx=ast.Load()),
                    slice=generate_input_annotation(
                        type.of_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    ),
                    ctx=ast.Load(),
                ),
                ctx=ast.Load(),
            )

        registry.register_import("typing.List")
        return ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()),
            slice=generate_input_annotation(
                type.of_type, parent, config, plugin_config, registry, is_optional=True
            ),
            ctx=ast.Load(),
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

    for base in plugin_config.inputtype_bases:
        registry.register_import(base)

    for key, type in inputobjects_type.items():

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
                        keywords=[
                            ast.keyword(
                                arg="alias", value=ast.Constant(value=value_key)
                            )
                        ],
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
                bases=[
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.inputtype_bases
                ]
                + additional_bases,
                decorator_list=[],
                keywords=[],
                body=fields + generate_config_class(config, typename=key),
            )
        )

    return tree


class InputsPlugin(Plugin):
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
