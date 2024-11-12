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
from turms.utils import parse_documents
from turms.registry import ClassRegistry


class EnumsPluginsError(Exception):
    pass


class EnumsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PLUGINS_ENUMS_")
    type: str = "turms.plugins.enums.EnumsPlugin"
    skip_underscore: bool = False
    skip_double_underscore: bool = True
    skip_unreferenced: bool = True
    prepend: str = ""
    append: str = ""


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

    if plugin_config.skip_unreferenced and config.documents:
        ref_registry = create_reference_registry_from_documents(
            client_schema, parse_documents(client_schema, config.documents)
        )
    else:
        ref_registry = None

    for key, type in enum_types.items():
        if ref_registry and key not in ref_registry.enums:
            continue

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        if plugin_config.skip_double_underscore and key.startswith("__"):
            continue

        classname = registry.generate_enum(key)

        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

        for value_key, value in type.values.items():
            if isinstance(value.value, str):
                servalue = value.value
            else:
                servalue = value.value.value

            assign = ast.Assign(
                targets=[ast.Name(id=str(value_key), ctx=ast.Store())],
                value=ast.Constant(value=servalue),
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
                classname,
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
    """The Enum plugin generates python enums from the GraphQL schema.

    It does not need documents but generates every enum from the loaded schema.

    By providing a config, you can skip enums that start with an underscore and
    prepend and append strings to the generated enums."""

    config: EnumsPluginConfig = Field(default_factory=EnumsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        registry.register_import("enum.Enum")

        return generate_enums(client_schema, config, self.config, registry)
