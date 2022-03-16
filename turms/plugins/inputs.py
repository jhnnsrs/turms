from graphql import (
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
    GraphQLWrappingType,
)
from turms.plugins.base import Plugin, PluginConfig
import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import BaseModel, BaseSettings, Field
from graphql.type.definition import (
    GraphQLEnumType,
)
import keyword
from turms.registry import ClassRegistry


class InputsPluginConfig(PluginConfig):
    type = "turms.plugins.inputs.InputsPlugin"
    inputtype_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_INPUTS_"


def generate_input_annotation(
    type: GraphQLInputType,
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
                slice=ast.Name(
                    id=registry.get_scalar_equivalent(type.name), ctx=ast.Load()
                ),
            )
        else:
            return ast.Name(
                id=registry.get_scalar_equivalent(type.name),
                ctx=ast.Load(),
            )

    if isinstance(type, GraphQLInputObjectType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(value=registry.get_inputtype_class(type.name)),
            )
        return ast.Constant(
            value=registry.get_inputtype_class(type.name),
        )

    if isinstance(type, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(
                    value=registry.get_enum_class(type.name),
                ),
            )
        return ast.Constant(
            value=registry.get_enum_class(type.name),
        )
    if isinstance(type, GraphQLNonNull):
        return generate_input_annotation(
            type.of_type, config, plugin_config, registry, is_optional=False
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
                        type.of_type, config, plugin_config, registry, is_optional=True
                    ),
                    ctx=ast.Load(),
                ),
            )

        registry.register_import("typing.List")
        return ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()),
            slice=generate_input_annotation(
                type.of_type, config, plugin_config, registry, is_optional=True
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

    self_referential = set()

    for key, type in inputobjects_type.items():

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        name = registry.generate_inputtype_classname(key)
        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

        for value_key, value in type.fields.items():

            if isinstance(value.type, GraphQLInputObjectType):
                self_referential.add(name)

            field_name = registry.generate_node_name(value_key)

            if field_name != value_key:
                registry.register_import("pydantic.Field")
                assign = ast.AnnAssign(
                    target=ast.Name(field_name, ctx=ast.Store()),
                    annotation=generate_input_annotation(
                        value.type, config, plugin_config, registry, is_optional=True
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
                        value.type, config, plugin_config, registry, is_optional=True
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

        registry.register_inputtype_class(key, name)

        tree.append(
            ast.ClassDef(
                name,
                bases=[
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.inputtype_bases
                ],
                decorator_list=[],
                keywords=[],
                body=fields,
            )
        )

    for input_name in self_referential:
        tree.append(
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(
                            id=input_name,
                            ctx=ast.Load(),
                        ),
                        attr="update_forward_refs",
                        ctx=ast.Load(),
                    ),
                    keywords=[],
                    args=[],
                )
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
