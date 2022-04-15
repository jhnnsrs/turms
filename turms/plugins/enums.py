from turms.plugins.base import Plugin, PluginConfig
import ast
from typing import List, Dict, Optional, Union, Tuple, Type
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import Field
from graphql.type.definition import (
    GraphQLEnumType, GraphQLNamedType, GraphQLEnumValue,
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


class AstGenerator:
    @staticmethod
    def _generate_description(description: str) -> ast.Expr:
        return ast.Expr(value=ast.Constant(value=description))

    @staticmethod
    def generate_type_description(
            description: str
    ) -> ast.Expr:
        return AstGenerator._generate_description(description)

    @staticmethod
    def generate_field_description(
            description: str
    ) -> ast.Expr:
        return AstGenerator._generate_description(description)

    @staticmethod
    def generate_enum_value(
            field_name: str,
            enum_value: str
    ) -> ast.Assign:
        return ast.Assign(
            targets=[ast.Name(id=field_name, ctx=ast.Store())],
            value=ast.Constant(value=enum_value)
        )

    @staticmethod
    def generate_enum_class_definition(
            classname: str,
            enum_values: List[ast.AST]
    ) -> ast.ClassDef:
        return ast.ClassDef(
            classname,
            bases=[
                ast.Name(id="str", ctx=ast.Load()),
                ast.Name(id="Enum", ctx=ast.Load()),
            ],
            decorator_list=[],
            keywords=[],
            body=enum_values,
        )


class EnumsPlugin(Plugin):
    config: EnumsPluginConfig = Field(default_factory=EnumsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

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

    def _get_types_from_schema(
            self,
            client_schema: GraphQLSchema,
            class_or_tuple: Union[Type[GraphQLNamedType], Tuple[Type[GraphQLNamedType]]],
    ) -> Dict[str, GraphQLEnumType]:
        return {
            key: value
            for key, value in client_schema.type_map.items()
            if isinstance(value, class_or_tuple)
        }

    def _skip_type(self, typename: str) -> bool:
        return self.config.skip_underscore and typename.startswith("_")

    def _generate_enum_class_definition(
            self,
            typename: str,
            gql_type: GraphQLEnumType,
            registry: ClassRegistry
    ) -> ast.ClassDef:
        classname = self._generate_classname(registry, typename)
        enum_values = self._generate_enum_values(gql_type)
        return AstGenerator.generate_enum_class_definition(classname, enum_values)

    def _generate_classname(self, registry: ClassRegistry, typename: str) -> str:
        return registry.generate_enum(typename)

    def _generate_enum_values(self, gql_type: GraphQLEnumType) -> List[ast.AST]:
        enum_value_definitions: List[ast] = []
        if self._type_has_description(gql_type):
            enum_value_definitions.append(self._generate_type_description(gql_type))

        for enum_key, enum_value in gql_type.values.items():
            enum_value_definitions.append(self._generate_enum_value(enum_key, enum_value))
            if self._enum_value_has_description(enum_value):
                enum_value_definitions.append(self._generate_enum_value_description(enum_value))

        return enum_value_definitions

    def _type_has_description(self, gql_type: GraphQLNamedType) -> bool:
        return gql_type.description is not None

    def _generate_type_description(self, gql_type: GraphQLNamedType) -> ast.Expr:
        return AstGenerator.generate_type_description(gql_type.description)

    def _generate_enum_value(self, enum_key: str, enum_value: GraphQLEnumValue) -> ast.Assign:
        return AstGenerator.generate_enum_value(enum_key, enum_value.value)

    def _enum_value_has_description(self, enum_value: GraphQLEnumValue) -> bool:
        return enum_value.description is not None or enum_value.deprecation_reason is not None

    def _generate_enum_value_description(self, enum_value: GraphQLEnumValue) -> ast.Expr:
        if enum_value.deprecation_reason is not None:
            comment = f"DEPRECATED: {enum_value.deprecation_reason}"
        else:
            comment = enum_value.description
        return AstGenerator.generate_field_description(comment)
