import ast
from collections import defaultdict
from typing import Dict, List, Union, DefaultDict

from graphql import (
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLSchema,
)
from pydantic import Field

from turms.ast_generators import ObjectTypeAstGenerator
from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.base import Plugin, PluginConfig
from turms.registry import ClassRegistry
from turms.utils import (
    interface_is_extended_by_other_interfaces,
)


class ObjectsPluginConfig(PluginConfig):
    type = "turms.plugins.objects.ObjectsPlugin"
    types_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = False
    skip_double_underscore: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_OBJECTS_"


class ObjectsPlugin(Plugin):
    config: ObjectsPluginConfig = Field(default_factory=ObjectsPluginConfig)
    _interface_to_implementations_map: DefaultDict[str, List[str]]
    _interface_to_generated_classname_map: Dict[str, str]

    class Config:
        underscore_attrs_are_private = True

    def generate_ast(
            self,
            client_schema: GraphQLSchema,
            config: GeneratorConfig,
            registry: ClassRegistry,
    ) -> List[ast.AST]:
        return self._generate_types(client_schema, config, registry)

    def _generate_types(
            self,
            schema: GraphQLSchema,
            config: GeneratorConfig,
            registry: ClassRegistry
    ) -> List[ast.AST]:
        self._interface_to_implementations_map = defaultdict(list)
        self._interface_to_generated_classname_map = {}

        types_ast: List[ast.AST] = []
        interfaces = self._get_types_from_schema(schema, GraphQLInterfaceType)
        objects = self._get_types_from_schema(schema, GraphQLObjectType)

        for typename, gql_type in {**interfaces, **objects}.items():
            if self._skip_type(typename):
                continue
            types_ast.append(
                self._generate_class_definition(gql_type, config, registry)
            )

        # Check unimplemented interfaces
        types_ast.extend(self._generate_interface_implementations(config, registry))

        return types_ast

    def _skip_type(self, typename: str) -> bool:
        if self.config.skip_underscore and typename.startswith("_"):
            return True
        if self.config.skip_double_underscore and typename.startswith("__"):
            return True
        return False

    def _generate_class_definition(
            self,
            gql_type: Union[GraphQLInterfaceType, GraphQLObjectType],
            config: GeneratorConfig,
            registry: ClassRegistry
    ) -> ast.ClassDef:
        typename = gql_type.name
        classname = self._generate_classname(gql_type, registry)
        if isinstance(gql_type, GraphQLInterfaceType):
            self._interface_to_generated_classname_map[typename] = classname
        base_classes = self._generate_base_classes(classname, gql_type, config, registry)
        body = self._generate_type_body(gql_type, config, registry)
        return ObjectTypeAstGenerator.generate_class_definition(classname, base_classes, body)

    @staticmethod
    def _generate_classname(gql_type: Union[GraphQLObjectType, GraphQLInterfaceType], registry: ClassRegistry) -> str:
        if isinstance(gql_type, GraphQLObjectType):
            return registry.generate_objecttype(gql_type.name)
        if isinstance(gql_type, GraphQLInterfaceType):
            return registry.generate_interface(gql_type.name)
        raise NotImplementedError  # pragma: no cover

    def _generate_base_classes(
            self,
            classname: str,
            gql_type: Union[GraphQLObjectType, GraphQLInterfaceType],
            config: GeneratorConfig,
            registry: ClassRegistry,
    ) -> List[str]:
        base_classes = self.config.types_bases
        additional_base_classes = self._get_additional_base_classes(gql_type, config)
        importable_base_classes = base_classes + additional_base_classes
        for base in importable_base_classes:
            registry.register_import(base)
        interface_base_classes = self._get_interface_base_classes(classname, gql_type, registry)
        return interface_base_classes + importable_base_classes

    def _get_interface_base_classes(
            self,
            classname: str,
            gql_type: Union[GraphQLObjectType, GraphQLInterfaceType],
            registry: ClassRegistry,
    ) -> List[str]:
        base_classes = []
        for interface in gql_type.interfaces:
            self._interface_to_implementations_map[interface.name].append(classname)
            other_interfaces = set(gql_type.interfaces)
            if not interface_is_extended_by_other_interfaces(interface, other_interfaces):
                base_classes.append(registry.inherit_interface(interface.name))
        return base_classes

    def _generate_type_body(
            self,
            gql_type: Union[GraphQLObjectType, GraphQLInterfaceType],
            config: GeneratorConfig,
            registry: ClassRegistry,
    ) -> List[ast.AST]:
        body: List[ast.AST] = []
        if self._type_has_description(gql_type):
            body.append(self._generate_type_description_ast(gql_type))
        for field_name, field_value in gql_type.fields.items():
            attribute_name = registry.generate_node_name(field_name)
            if attribute_name != field_name:
                alias = ObjectTypeAstGenerator.generate_field_alias(field_name)
            else:
                alias = None
            annotation = generate_object_field_annotation(
                field_value.type,
                gql_type.name,
                config,
                self.config,
                registry,
                is_optional=True
            )
            body.append(ObjectTypeAstGenerator.generate_attribute(attribute_name, annotation, alias))
            if self._field_has_description(field_value):
                body.append(self._generate_field_description(field_value))
        return body

    def _field_has_description(self, field: GraphQLField) -> bool:
        return field.description is not None or field.deprecation_reason is not None

    def _generate_field_description(self, field: GraphQLField) -> ast.Expr:
        if not field.deprecation_reason:
            comment = field.description
        else:
            comment = f"DEPRECATED: {field.deprecation_reason}"
        return ObjectTypeAstGenerator.generate_field_description(comment)

    def _generate_interface_implementations(self, config: GeneratorConfig, registry: ClassRegistry) -> List[ast.AST]:
        implementations_ast: List[ast.AST] = []
        for interface, implementations in sorted(self._interface_to_implementations_map.items()):
            if implementations:
                registry.register_import("typing.Union")
                implementations_ast.append(
                    ObjectTypeAstGenerator.generate_interface_implementations(interface, sorted(implementations))
                )

        interfaces_without_implementations = {
            interface: base_class
            for interface, base_class in self._interface_to_generated_classname_map.items()
            if interface not in self._interface_to_implementations_map
        }
        if interfaces_without_implementations:
            if config.always_resolve_interfaces:
                raise GenerationError(
                    f"Interfaces {interfaces_without_implementations.keys()} have no types implementing it. "
                    f"And we have set always_resolve_interfaces to true. "
                    f"Make sure your schema is correct"
                )
            for interface, base_class in sorted(interfaces_without_implementations.items()):
                registry.warn(f"Interface {interface} has no types implementing it")
                implementations_ast.append(
                    ObjectTypeAstGenerator.generate_interface_without_implementation(interface, base_class)
                )
        return implementations_ast


def generate_object_field_annotation(
        graphql_type: GraphQLType,
        parent: str,
        config: GeneratorConfig,
        plugin_config: ObjectsPluginConfig,
        registry: ClassRegistry,
        is_optional=True,
):
    if isinstance(graphql_type, GraphQLScalarType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(graphql_type.name),
                ctx=ast.Load(),
            )

        return registry.reference_scalar(graphql_type.name)

    if isinstance(graphql_type, GraphQLInterfaceType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_interface(graphql_type.name, parent),
                ctx=ast.Load(),
            )

        return registry.reference_interface(graphql_type.name, parent)

    if isinstance(graphql_type, GraphQLObjectType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_object(graphql_type.name, parent),
                ctx=ast.Load(),
            )
        return registry.reference_object(graphql_type.name, parent)

    if isinstance(graphql_type, GraphQLUnionType):
        if is_optional:
            registry.register_import("typing.Optional")
            registry.register_import("typing.Union")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("Union", ctx=ast.Load()),
                    slice=ast.Tuple(
                        elts=[
                            generate_object_field_annotation(
                                union_type,
                                parent,
                                config,
                                plugin_config,
                                registry,
                                is_optional=False,
                            )
                            for union_type in graphql_type.types
                        ],
                        ctx=ast.Load(),
                    ),
                ),
                ctx=ast.Load(),
            )
        registry.register_import("typing.Union")

        return ast.Subscript(
            value=ast.Name("Union", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[
                    generate_object_field_annotation(
                        union_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=False,
                    )
                    for union_type in graphql_type.types
                ],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        )

    if isinstance(graphql_type, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_enum(
                    graphql_type.name,
                    parent,
                    allow_forward=not config.force_plugin_order,
                ),
                ctx=ast.Load(),
            )
        return registry.reference_enum(
            graphql_type.name, parent, allow_forward=not config.force_plugin_order
        )

    if isinstance(graphql_type, GraphQLNonNull):
        return generate_object_field_annotation(
            graphql_type.of_type,
            parent,
            config,
            plugin_config,
            registry,
            is_optional=False,
        )

    if isinstance(graphql_type, GraphQLList):
        if is_optional:
            registry.register_import("typing.Optional")
            registry.register_import("typing.List")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("List", ctx=ast.Load()),
                    slice=generate_object_field_annotation(
                        graphql_type.of_type,
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
            slice=generate_object_field_annotation(
                graphql_type.of_type,
                parent,
                config,
                plugin_config,
                registry,
                is_optional=True,
            ),
            ctx=ast.Load(),
        )

    raise NotImplementedError(f"Unknown input type {repr(graphql_type)}")  # pragma: no cover
