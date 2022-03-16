from turms.plugins.base import Plugin, PluginConfig
from abc import abstractmethod
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


class EnumsPluginsError(Exception):
    pass


class EnumsPluginConfig(PluginConfig):
    type = "turms.plugins.enums.EnumsPlugin"
    skip_underscore: bool = True
    prepend: str = ""
    append: str = ""

    class Config:
        env_prefix = "TURMS_PLUGINS_ENUMS_"


def generate_enums(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: EnumsPluginConfig,
    registry: ClassRegistry,
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

        name = registry.generate_enum_classname(key)
        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

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

        registry.register_enum_class(key, name)
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
    config: EnumsPluginConfig = Field(default_factory=EnumsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        registry.register_import("enum.Enum")

        return generate_enums(client_schema, config, self.config, registry)
