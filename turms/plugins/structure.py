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
from turms.plugins.fragments import generate_fragment
import re
from graphql import language, parse, get_introspection_query, validate
from turms.utils import (
    NoDocumentsFoundError,
    parse_documents,
    fragment_searcher,
    replace_iteratively,
)
import logging


logger = logging.getLogger(__name__)


class StructurePluginsConfig(BaseModel):
    query_bases: List[str] = ["herre.access.GraphQLQuery"]
    mutation_bases: List[str] = ["herre.access.GraphQLMutation"]

    structure_bases: List[str] = ["herre.access.GraphQLStructure"]

    prepend: str = ""
    append: str = ""
    structure_glob: Optional[str]


def generate_structure(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: StructurePluginsConfig,
):

    tree = []

    x = get_operation_root_type(client_schema, o)
    query_fields = []
    name = f"{plugin_config.prepend}{o.name.value}{plugin_config.append}"

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
                    targets=[ast.Name(id="ward", ctx=ast.Store())],
                    value=ast.Constant(value=str("arkitekt")),
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


class StructurePlugin(Plugin):
    def __init__(self, config=None):
        self.plugin_config = config or StructurePluginsConfig()

    def generate_imports(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        imports = []

        all_bases = (
            self.plugin_config.query_bases
            + self.plugin_config.mutation_bases
            + self.plugin_config.structure_bases
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
                client_schema, self.plugin_config.structure_glob
            )
        except NoDocumentsFoundError as e:
            logger.exception(e)
            return plugin_tree

        definitions = documents.definitions

        fragments = [
            node for node in definitions if isinstance(node, FragmentDefinitionNode)
        ]

        for fragment in fragments:
            plugin_tree += generate_fragment(
                fragment, client_schema, config, self.plugin_config
            )

        operations = [
            node for node in definitions if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            if operation.operation == OperationType.QUERY:
                plugin_tree += generate_structure(
                    operation, client_schema, config, self.plugin_config
                )

        return plugin_tree
