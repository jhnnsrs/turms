import ast
from typing import List

from graphql import (
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
    GraphQLEnumType,
    GraphQLNamedType,
    GraphQLInputField,
    GraphQLSchema,
)
from pydantic import Field

from turms.ast_generators import AnnotationAstGenerator, InputTypeAstGenerator
from turms.config import GeneratorConfig
from turms.plugins.base import Plugin, PluginConfig
from turms.registry import ClassRegistry


class InputsPluginConfig(PluginConfig):
    type = "turms.plugins.inputs.InputsPlugin"
    inputtype_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_INPUTS_"


class InputsPlugin(Plugin):
    config: InputsPluginConfig = Field(default_factory=InputsPluginConfig)

    def generate_ast(
            self,
            client_schema: GraphQLSchema,
            config: GeneratorConfig,
            registry: ClassRegistry,
    ) -> List[ast.AST]:
        inputs_ast: List[ast.AST] = []

        inputs = self._get_types_from_schema(client_schema, GraphQLInputObjectType)
        for typename, gql_type in inputs.items():
            if self._skip_type(typename):
                continue
            inputs_ast.append(
                self._generate_input_class_definition(typename, gql_type, config, registry)
            )
        return inputs_ast

    def _skip_type(self, typename: str):
        return self.config.skip_underscore and typename.startswith("_")

    def _generate_input_class_definition(
            self,
            typename: str,
            gql_type: GraphQLInputObjectType,
            config: GeneratorConfig,
            registry: ClassRegistry
    ) -> ast.ClassDef:
        classname = self._generate_classname(typename, registry)
        base_classes = self._generate_base_classes(gql_type, config, registry)
        input_body = self._generate_input_body(gql_type, config, registry)
        return InputTypeAstGenerator.generate_class_definition(classname, base_classes, input_body)

    def _generate_classname(self, typename: str, registry: ClassRegistry):
        return registry.generate_inputtype(typename)

    def _generate_base_classes(
            self,
            gql_type: GraphQLInputObjectType,
            config: GeneratorConfig,
            registry: ClassRegistry
    ) -> List[str]:
        base_classes = self.config.inputtype_bases
        additional_base_classes = self._get_additional_base_classes(gql_type, config)
        all_base_classes = base_classes + additional_base_classes
        for base in all_base_classes:
            registry.register_import(base)
        return all_base_classes

    def _generate_input_body(
            self,
            gql_type: GraphQLInputObjectType,
            config: GeneratorConfig,
            registry: ClassRegistry
    ) -> List[ast.AST]:
        body: List[ast.AST] = []
        if self._type_has_description(gql_type):
            body.append(self._generate_type_description_ast(gql_type))

        for field_name, field_value in gql_type.fields.items():
            body.append(
                self._generate_input_field_attribute_ast(gql_type.name, field_name, field_value, config, registry))
            if self._input_field_has_description(field_value):
                body.append(self._generate_input_field_description_ast(field_value))
        return body

    def _generate_input_field_attribute_ast(
            self,
            parent_name: str,
            field_name: str,
            field_value: GraphQLInputField,
            config: GeneratorConfig,
            registry: ClassRegistry
    ) -> ast.AnnAssign:
        attribute_name = self._generate_attribute_name(field_name, registry)
        annotation = self._generate_attribute_annotation_ast(parent_name, field_value, config, registry)
        if attribute_name != field_name:
            alias = self._generate_attribute_alias_ast(field_name, registry)
        else:
            alias = None
        return InputTypeAstGenerator.generate_attribute(attribute_name, annotation, alias)

    def _generate_attribute_name(self, field_name: str, registry: ClassRegistry) -> str:
        return registry.generate_node_name(field_name)

    def _generate_attribute_annotation_ast(
            self,
            parent_name: str,
            field_value: GraphQLInputField,
            config: GeneratorConfig,
            registry: ClassRegistry,
    ) -> ast.AST:
        return generate_input_field_annotation(
            graphql_type=field_value.type,
            parent=parent_name,
            config=config,
            plugin_config=self.config,
            registry=registry,
            is_optional=True
        )

    def _generate_attribute_alias_ast(self, original_name: str, registry: ClassRegistry) -> ast.Call:
        registry.register_import("pydantic.Field")
        return InputTypeAstGenerator.generate_field_alias(original_name)

    def _input_field_has_description(self, field: GraphQLInputField):
        return field.description is not None or field.deprecation_reason is not None

    def _generate_input_field_description_ast(self, field: GraphQLInputField) -> ast.AST:
        if not field.deprecation_reason:
            comment = field.description
        else:
            comment = f"DEPRECATED: {field.deprecation_reason}"
        return InputTypeAstGenerator.generate_field_description(comment)


def generate_input_field_annotation(
        graphql_type: GraphQLInputType,
        parent: str,
        config: GeneratorConfig,
        plugin_config: InputsPluginConfig,
        registry: ClassRegistry,
        is_optional=True,
) -> ast.AST:
    if isinstance(graphql_type, GraphQLScalarType):
        annotation = registry.reference_scalar(graphql_type.name)

    elif isinstance(graphql_type, GraphQLInputObjectType):
        annotation = registry.reference_inputtype(graphql_type.name, parent)

    elif isinstance(graphql_type, GraphQLEnumType):
        annotation = registry.reference_enum(graphql_type.name, parent, allow_forward=not config.force_plugin_order)

    elif isinstance(graphql_type, GraphQLNonNull):
        annotation = generate_input_field_annotation(
            graphql_type.of_type, parent, config, plugin_config, registry, is_optional=False
        )
        is_optional = False

    elif isinstance(graphql_type, GraphQLList):
        registry.register_import("typing.List")
        annotation = AnnotationAstGenerator.list(
            generate_input_field_annotation(
                graphql_type.of_type,
                parent,
                config,
                plugin_config,
                registry,
                is_optional=True,
            )
        )
    else:
        raise NotImplementedError(f"Unknown input type {graphql_type}")  # pragma: no cover

    if is_optional:
        registry.register_import("typing.Optional")
        annotation = AnnotationAstGenerator.optional(annotation)
    return annotation
