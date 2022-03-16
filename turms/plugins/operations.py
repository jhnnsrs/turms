from abc import abstractmethod
import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.language.ast import OperationDefinitionNode, OperationType
from turms.recurse import recurse_annotation, type_field_node
from turms.plugins.base import Plugin, PluginConfig
from pydantic import BaseModel, BaseSettings, Field
from graphql.error.graphql_error import GraphQLError
from graphql.error.syntax_error import GraphQLSyntaxError
from graphql.language.ast import (
    DefinitionNode,
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    ListTypeNode,
    NonNullTypeNode,
    OperationDefinitionNode,
    OperationType,
    SelectionNode,
    SelectionSetNode,
)
from graphql.type.definition import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    get_named_type,
    is_list_type,
)
from graphql.type.validate import get_operation_type_node
from graphql.utilities.build_client_schema import build_client_schema, GraphQLSchema
from graphql.utilities.get_operation_root_type import get_operation_root_type
from graphql.utilities.type_info import TypeInfo, get_field_def

from pydantic.main import BaseModel
import re
from graphql import language, parse, get_introspection_query, validate
from turms.registry import ClassRegistry
from turms.utils import (
    NoDocumentsFoundError,
    generate_config_class,
    parse_documents,
    replace_iteratively,
)
import logging


logger = logging.getLogger(__name__)
fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


class OperationsPluginConfig(PluginConfig):
    type = "turms.plugins.operations.OperationsPlugin"
    query_bases: List[str] = None
    mutation_bases: List[str] = None
    subscription_bases: List[str] = None
    operations_glob: Optional[str]

    class Config:
        env_prefix = "TURMS_PLUGINS_OPERATIONS_"


def get_query_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.query_bases:
        for base in plugin_config.query_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.query_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def get_mutation_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.mutation_bases:
        for base in plugin_config.mutation_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.mutation_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def get_subscription_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.subscription_bases:
        for base in plugin_config.subscription_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.subscription_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def generate_operation(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    tree = []
    assert o.name.value, "Operation names are required"

    if o.operation == OperationType.MUTATION:
        class_name = registry.generate_mutation_classname(o.name.value)
        extra_bases = get_mutation_bases(config, plugin_config, registry)
    if o.operation == OperationType.SUBSCRIPTION:
        class_name = registry.generate_subscription_classname(o.name.value)
        extra_bases = get_subscription_bases(config, plugin_config, registry)
    if o.operation == OperationType.QUERY:
        class_name = registry.generate_query_classname(o.name.value)
        extra_bases = get_query_bases(config, plugin_config, registry)

    x = get_operation_root_type(client_schema, o)
    operation_fields = []

    for field_node in o.selection_set.selections:

        field_node: FieldNode = field_node
        field_definition = get_field_def(client_schema, x, field_node)
        assert field_definition, "Couldn't find field definition"

        operation_fields += [
            type_field_node(
                field_node,
                field_definition,
                client_schema,
                config,
                tree,
                registry,
                parent_name=class_name,
            ),
        ]

    query_document = language.print_ast(o)
    z = fragment_searcher.findall(query_document)

    merged_document = replace_iteratively(query_document, registry)

    operation_fields += [
        ast.ClassDef(
            "Meta",
            bases=[],
            decorator_list=[],
            keywords=[],
            body=[
                ast.Assign(
                    targets=[ast.Name(id="domain", ctx=ast.Store())],
                    value=ast.Constant(value=str(config.domain)),
                ),
                ast.Assign(
                    targets=[ast.Name(id="document", ctx=ast.Store())],
                    value=ast.Constant(value=merged_document),
                ),
            ],
        )
    ]

    tree.append(
        ast.ClassDef(
            class_name,
            bases=extra_bases,
            decorator_list=[],
            keywords=[],
            body=operation_fields + generate_config_class(config),
        )
    )

    return tree


class OperationsPlugin(Plugin):
    config: OperationsPluginConfig = Field(default_factory=OperationsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        plugin_tree = []

        try:
            documents = parse_documents(
                client_schema, self.config.operations_glob or config.documents
            )
        except NoDocumentsFoundError as e:
            logger.exception(e)
            return plugin_tree

        definitions = documents.definitions
        operations = [
            node for node in definitions if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            plugin_tree += generate_operation(
                operation, client_schema, config, self.config, registry
            )

        return plugin_tree
