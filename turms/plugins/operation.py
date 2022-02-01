from abc import abstractmethod
import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.language.ast import OperationDefinitionNode, OperationType
from turms.parser.recurse import recurse_annotation
from turms.plugins.base import Plugin
from pydantic import BaseModel
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
from turms.utils import (
    NoDocumentsFoundError,
    parse_documents,
    replace_iteratively,
)
import logging


logger = logging.getLogger(__name__)
fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


class OperationsPluginConfig(BaseModel):
    query_bases: List[str] = ["turms.types.operation.GraphQLQuery"]
    mutation_bases: List[str] = ["turms.types.operation.GraphQLMutation"]
    subscription_bases: List[str] = ["turms.types.operation.GraphQLSubscription"]
    operations_glob: Optional[str]


def generate_query(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
):

    tree = []

    x = get_operation_root_type(client_schema, o)
    query_fields = []
    name = f"{config.prepend_query}{o.name.value.capitalize()}{config.append_query}"

    for field_node in o.selection_set.selections:

        field_node: FieldNode = field_node
        field_definition = get_field_def(client_schema, x, field_node)
        assert field_definition, "Couldn't find field definition"

        target = (
            field_node.alias.value
            if hasattr(field_node, "alias") and field_node.alias
            else field_node.name.value
        )

        query_fields += [
            ast.AnnAssign(
                target=ast.Name(target, ctx=ast.Store()),
                annotation=recurse_annotation(
                    field_node,
                    field_definition.type,
                    client_schema,
                    config,
                    tree,
                    parent_name=name,
                ),
                simple=1,
            )
        ]

    query_document = language.print_ast(o)
    z = fragment_searcher.findall(query_document)

    merged_document = replace_iteratively(query_document)

    query_fields += [
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
            name,
            bases=[
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in plugin_config.query_bases
            ],
            decorator_list=[],
            keywords=[],
            body=query_fields,
        )
    )

    return tree


def generate_mutation(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
):

    tree = []

    x = get_operation_root_type(client_schema, o)
    query_fields = []
    name = (
        f"{config.prepend_mutation}{o.name.value.capitalize()}{config.append_mutation}"
    )

    for field_node in o.selection_set.selections:

        field_node: FieldNode = field_node
        field_definition = get_field_def(client_schema, x, field_node)
        assert field_definition, "Couldn't find field definition"

        target = (
            field_node.alias.value
            if hasattr(field_node, "alias") and field_node.alias
            else field_node.name.value
        )

        query_fields += [
            ast.AnnAssign(
                target=ast.Name(target, ctx=ast.Store()),
                annotation=recurse_annotation(
                    field_node,
                    field_definition.type,
                    client_schema,
                    config,
                    tree,
                    parent_name=name,
                ),
                simple=1,
            )
        ]

    query_document = language.print_ast(o)
    z = fragment_searcher.findall(query_document)

    merged_document = replace_iteratively(query_document)

    query_fields += [
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
            name,
            bases=[
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in plugin_config.mutation_bases
            ],
            decorator_list=[],
            keywords=[],
            body=query_fields,
        )
    )

    return tree


def generate_subscription(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
):

    tree = []

    x = get_operation_root_type(client_schema, o)
    query_fields = []
    name = f"{config.prepend_subscription}{o.name.value.capitalize()}{config.append_subscription}"

    for field_node in o.selection_set.selections:

        field_node: FieldNode = field_node
        field_definition = get_field_def(client_schema, x, field_node)
        assert field_definition, "Couldn't find field definition"

        target = (
            field_node.alias.value
            if hasattr(field_node, "alias") and field_node.alias
            else field_node.name.value
        )

        query_fields += [
            ast.AnnAssign(
                target=ast.Name(target, ctx=ast.Store()),
                annotation=recurse_annotation(
                    field_node,
                    field_definition.type,
                    client_schema,
                    config,
                    tree,
                    parent_name=name,
                ),
                simple=1,
            )
        ]

    query_document = language.print_ast(o)
    z = fragment_searcher.findall(query_document)

    merged_document = replace_iteratively(query_document)

    query_fields += [
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
            name,
            bases=[
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in plugin_config.mutation_bases
            ],
            decorator_list=[],
            keywords=[],
            body=query_fields,
        )
    )

    return tree


class OperationsPlugin(Plugin):
    def __init__(self, config=None, **data):
        self.plugin_config = config or OperationsPluginConfig(**data)

    def generate_imports(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        imports = []

        all_bases = (
            self.plugin_config.query_bases
            + self.plugin_config.mutation_bases
            + self.plugin_config.subscription_bases
        )

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

        plugin_tree = []

        try:
            documents = parse_documents(
                client_schema, self.plugin_config.operations_glob or config.documents
            )
        except NoDocumentsFoundError as e:
            logger.exception(e)
            return plugin_tree

        definitions = documents.definitions
        operations = [
            node for node in definitions if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            if operation.operation == OperationType.QUERY:
                plugin_tree += generate_query(
                    operation, client_schema, config, self.plugin_config
                )
            if operation.operation == OperationType.MUTATION:
                plugin_tree += generate_mutation(
                    operation, client_schema, config, self.plugin_config
                )
            if operation.operation == OperationType.SUBSCRIPTION:
                plugin_tree += generate_subscription(
                    operation, client_schema, config, self.plugin_config
                )

        return plugin_tree
