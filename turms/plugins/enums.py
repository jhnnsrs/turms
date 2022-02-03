from turms.globals import ENUM_CLASS_MAP
from turms.plugins.base import Plugin
from abc import abstractmethod
import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import BaseModel
from graphql.type.definition import (
    GraphQLEnumType,
)
import keyword


class EnumsPluginsError(Exception):
    pass

class EnumsPluginConfig(BaseModel):
    skip_underscore: bool = True
    prepend: str = ""
    append: str = ""


def generate_enums(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: EnumsPluginConfig,
):

    tree = []

    enum_types = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLEnumType)
    }

    for key, type in enum_types.items():

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        name = f"{config.prepend_enum}{key}{config.append_enum}"
        fields = [ast.Expr(value=ast.Constant(value=type.description))] if type.description else []

        for value_key, value in type.values.items():
            if keyword.iskeyword(value_key):
                value_key = f"{value_key}_"


            assign = ast.Assign(
                targets=[ast.Name(id=str(value_key), ctx=ast.Store())],
                value=ast.Constant(value=value.value),
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


class EnumsPlugin(Plugin):
    def __init__(self, config=None, **data):
        self.plugin_config = config or EnumsPluginConfig(**data)

    def generate_imports(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        imports = []

        imports.append(
            ast.ImportFrom(
                module="enum",
                names=[ast.alias(name="Enum")],
                level=0,
            )
        )

        return imports

    def generate_body(
        self, client_schema: GraphQLSchema, config: GeneratorConfig
    ) -> List[ast.AST]:

        return generate_enums(client_schema, config, self.plugin_config)
