import ast
from typing import List

from graphql import (
    GraphQLSchema,
    GraphQLEnumType,
    GraphQLEnumValue,
)
from pydantic import Field

from turms.ast_generators import EnumTypeAstGenerator
from turms.config import GeneratorConfig
from turms.plugins.base import Plugin, PluginConfig
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


class EnumsPlugin(Plugin):
    config: EnumsPluginConfig = Field(default_factory=EnumsPluginConfig)

    def generate_ast(
            self,
            client_schema: GraphQLSchema,
            config: GeneratorConfig,
            registry: ClassRegistry,
    ) -> List[ast.AST]:

        # Todo: Remove, use self._generate_base_classes instead
        #  Unfortunately, this requires updating tests, because some tests
        #  test for the enum import even though their schema doesn't contain enums.
        registry.register_import("enum.Enum")

        return self._generate_enums(client_schema, config, registry)

    def _generate_enums(self, client_schema, config, registry) -> List[ast.AST]:
        enums_ast: List[ast.AST] = []
        enums = self._get_types_from_schema(client_schema, GraphQLEnumType)

        for typename, gql_type in enums.items():
            if self._skip_type(typename):
                continue
            enums_ast.append(
                self._generate_enum_class_definition(
                    typename, gql_type, registry
                )
            )

        return enums_ast

    def _skip_type(self, typename: str) -> bool:
        return self.config.skip_underscore and typename.startswith("_")

    def _generate_enum_class_definition(
            self,
            typename: str,
            gql_type: GraphQLEnumType,
            registry: ClassRegistry
    ) -> ast.ClassDef:
        classname = self._generate_classname(registry, typename)
        base_classes = self._generate_base_classes(registry)
        enum_body = self._generate_enum_body(gql_type)
        return EnumTypeAstGenerator.generate_class_definition(classname, base_classes, enum_body)

    def _generate_classname(self, registry: ClassRegistry, typename: str) -> str:
        return registry.generate_enum(typename)

    def _generate_base_classes(self, registry: ClassRegistry) -> List[str]:
        registry.register_import("enum.Enum")
        return ["str", "enum.Enum"]

    def _generate_enum_body(
            self,
            gql_type: GraphQLEnumType
    ) -> List[ast.AST]:
        body: List[ast.AST] = []
        if self._type_has_description(gql_type):
            body.append(self._generate_type_description_ast(gql_type))

        for enum_key, enum_value in gql_type.values.items():
            body.append(self._generate_enum_value_ast(enum_key, enum_value))
            if self._enum_value_has_description(enum_value):
                body.append(self._generate_enum_value_description_ast(enum_value))

        return body

    def _generate_enum_value_ast(self, enum_key: str, enum_value: GraphQLEnumValue) -> ast.Assign:
        return EnumTypeAstGenerator.generate_enum_value(enum_key, enum_value.value)

    def _enum_value_has_description(self, enum_value: GraphQLEnumValue) -> bool:
        return enum_value.description is not None or enum_value.deprecation_reason is not None

    def _generate_enum_value_description_ast(self, enum_value: GraphQLEnumValue) -> ast.Expr:
        if enum_value.deprecation_reason is not None:
            comment = f"DEPRECATED: {enum_value.deprecation_reason}"
        else:
            comment = enum_value.description
        return EnumTypeAstGenerator.generate_field_description(comment)
