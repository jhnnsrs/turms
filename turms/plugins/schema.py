from turms.globals import ENUM_CLASS_MAP
from turms.plugins.base import Plugin
from abc import abstractmethod
import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import BaseModel
from graphql.type.definition import GraphQLEnumType, GraphQLObjectType


class SchemaPluginConfig(BaseModel):
    skip_underscore: bool = True
    prepend: str = ""
    append: str = ""


def generate_schema(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: SchemaPluginConfig,
):

    tree = []

    enum_types = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLObjectType)
    }

    for key, type in enum_types.items():

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        name = f"{plugin_config.prepend}{key}{plugin_config.append}"
        fields = [ast.Expr(value=ast.Constant(value=type.description))] if type.description else []

        for value_key, value in type.values.items():
            assign = ast.Assign(
                targets=[ast.Name(id=str(value_key), ctx=ast.Store())],
                value=ast.Constant(value=str(value.value)),
            )

            potential_comment = (
                value.description
                if not value.is_deprecated
                else f"DEPRECATED: {value.description}"
            )

            if potential_comment:
                fields += [
                    assign,
                    ast.Expr(value=ast.Constant(value=potential_comment)),
                ]

            else:
                fields += [assign]

        ENUM_CLASS_MAP[key] = name
        tree.append(
            ast.ClassDef(
                name,
                bases=[
                    ast.Name(id="str", ctx=ast.Load()),
                    ast.Name(id="Enum", ctx=ast.Load()),
                ],
                decorator_list=[],
                keywords=[],
                body=fields,
            )
        )

    return tree


class SchemaPlugin(Plugin):
    def __init__(self, config=None, **data):
        self.plugin_config = config or SchemaPluginConfig(**data)

    def generate_body(
        self, client_schema: GraphQLSchema, config: GeneratorConfig
    ) -> List[ast.AST]:

        raise NotImplementedError("Not yet supported")
