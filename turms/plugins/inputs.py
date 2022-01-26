from graphql import (
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
    GraphQLWrappingType,
)
from turms.globals import INPUTTYPE_CLASS_MAP
from turms.plugins.base import Plugin
import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import BaseModel
from graphql.type.definition import (
    GraphQLEnumType,
)

from turms.utils import get_scalar_equivalent


class InputsPluginConfig(BaseModel):
    inputtype_bases: List[str] = ["turms.types.object.GraphQLInputObject"]
    skip_underscore: bool = True
    prepend: str = ""
    append: str = "Input"


def generate_input_annotation(
    type: GraphQLInputType,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    is_optional=True,
):
    if isinstance(type, GraphQLScalarType):
        if is_optional:
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Name(
                    id=get_scalar_equivalent(type.name, config), ctx=ast.Load()
                ),
            )
        else:
            return ast.Name(
                id=get_scalar_equivalent(type.name, config),
                ctx=ast.Load(),
            )

    if isinstance(type, GraphQLInputObjectType):
        if is_optional:
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(
                    value=f"{config.prepend_input}{type.name}{config.append_input}",
                ),
            )
        return ast.Constant(
            value=f"{config.prepend_input}{type.name}{config.append_input}",
        )

    if isinstance(type, GraphQLEnumType):
        if is_optional:
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(
                    value=f"{config.prepend_enum}{type.name}{config.append_enum}",
                ),
            )
        return ast.Constant(
            value=f"{config.prepend_enum}{type.name}{config.append_enum}",
        )
    if isinstance(type, GraphQLNonNull):
        return generate_input_annotation(
            type.of_type, config, plugin_config, is_optional=False
        )

    if isinstance(type, GraphQLList):
        if is_optional:
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("List", ctx=ast.Load()),
                    slice=generate_input_annotation(
                        type.of_type, config, plugin_config, is_optional=True
                    ),
                    ctx=ast.Load(),
                ),
            )

        return ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()),
            slice=generate_input_annotation(
                type.of_type, config, plugin_config, is_optional=True
            ),
            ctx=ast.Load(),
        )

    raise NotImplementedError(f"Unknown input type {type}")


def generate_inputs(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
):

    tree = []

    inputobjects_type = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLInputObjectType)
    }

    self_referential = []

    for key, type in inputobjects_type.items():

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        name = f"{config.prepend_input}{key}{config.append_input}"
        fields = [ast.Expr(value=ast.Constant(value=type.description))]

        for value_key, value in type.fields.items():

            if isinstance(value.type, GraphQLInputObjectType):
                self_referential.append(name)

            assign = ast.AnnAssign(
                target=ast.Name(value_key, ctx=ast.Store()),
                annotation=generate_input_annotation(
                    value.type, config, plugin_config, is_optional=True
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

        INPUTTYPE_CLASS_MAP[key] = name
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
    def __init__(self, config=None, **data):
        self.plugin_config = config or InputsPluginConfig(**data)

    def generate_imports(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        imports = []

        all_bases = self.plugin_config.inputtype_bases

        for item in all_bases:
            imports.append(
                ast.ImportFrom(
                    module=".".join(item.split(".")[:-1]),
                    names=[ast.alias(name=item.split(".")[-1])],
                    level=0,
                )
            )

        return imports

    def generate_body(
        self, client_schema: GraphQLSchema, config: GeneratorConfig
    ) -> List[ast.AST]:

        return generate_inputs(client_schema, config, self.plugin_config)
