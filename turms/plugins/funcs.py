from abc import abstractmethod
import ast
from typing import List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import BaseModel
from graphql.language.ast import OperationDefinitionNode, OperationType
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import BaseModel
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
from turms.utils import (
    NoDocumentsFoundError,
    generate_typename_field,
    get_scalar_equivalent,
    parse_documents,
    target_from_node,
)
import re
import ast

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
from graphql.utilities.get_operation_root_type import get_operation_root_type
from graphql.utilities.type_info import TypeInfo, get_field_def
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class OperationsFuncPluginConfig(BaseModel):
    generate_async: bool = True
    generate_sync: bool = True

    funcs_glob: Optional[str]


def generate_query_args(
    o: OperationDefinitionNode, client_schema: GraphQLSchema, config: GeneratorConfig
):

    pos_args = []

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type.type, ListTypeNode):
                raise NotImplementedError()
            else:
                pos_args.append(
                    ast.arg(
                        arg=v.variable.name.value,
                        annotation=ast.Name(
                            id=get_scalar_equivalent(v.type.type.name.value, config),
                            ctx=ast.Load(),
                        ),
                    )
                )

    kw_args = []
    kw_values = []
    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type, ListTypeNode):
                raise NotImplementedError()
            else:
                kw_args.append(
                    ast.arg(
                        arg=v.variable.name.value,
                        annotation=ast.Name(
                            id=get_scalar_equivalent(v.type.name.value, config),
                            ctx=ast.Load(),
                        ),
                    )
                )
                kw_values.append(ast.Constant(value=None))

    return ast.arguments(
        args=pos_args + kw_args,
        posonlyargs=[],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=kw_values,
    )


def generate_query_dict(
    o: OperationDefinitionNode, client_schema: GraphQLSchema, config: GeneratorConfig
):

    keys = []
    values = []

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type.type, ListTypeNode):
                raise NotImplementedError()
            else:
                keys.append(ast.Constant(value=v.variable.name.value))
                values.append(ast.Name(id=v.variable.name.value, ctx=ast.Load()))

    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type, ListTypeNode):
                raise NotImplementedError()
            else:
                keys.append(ast.Constant(value=v.variable.name.value))
                values.append(ast.Name(id=v.variable.name.value, ctx=ast.Load()))

    return ast.Dict(keys=keys, values=values)


def generate_query_doc(
    o: OperationDefinitionNode, client_schema: GraphQLSchema, config: GeneratorConfig
):

    pos_args = []
    x = get_operation_root_type(client_schema, o)

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type.type, ListTypeNode):
                raise NotImplementedError()
            else:
                pos_args.append(ast.arg(arg=v.variable.name.value))

    kw_args = []
    kw_values = []
    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type, ListTypeNode):
                raise NotImplementedError()
            else:
                kw_args.append(ast.arg(arg=v.variable.name.value))
                kw_values.append(ast.Constant(value=None))

    header = f"Query {o.name.value}  \n\n"

    query_descriptions = []

    for field in o.selection_set.selections:
        if isinstance(field, FieldNode):
            target = target_from_node(field)
            field_definition = get_field_def(client_schema, x, field)
            if field_definition.description:
                query_descriptions.append(f"{target}: {field_definition.description}")

    description = "\n ".join([header] + query_descriptions)

    return ast.Expr(value=ast.Constant(value=description))


def generate_operation_func(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
):
    tree = []

    if o.operation == OperationType.QUERY:
        o_name = f"{o.name.value}Query"
    if o.operation == OperationType.MUTATION:
        o_name = f"{o.name.value}Mutation"
    if o.operation == OperationType.SUBSCRIPTION:
        o_name = f"{o.name.value}Subscription"

    if plugin_config.generate_async:
        tree.append(
            ast.AsyncFunctionDef(
                name=f"ause{o.name.value}",
                args=generate_query_args(o, client_schema, config),
                body=[
                    generate_query_doc(o, client_schema, config),
                    ast.Return(
                        value=ast.Await(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(
                                        id=o_name,
                                        ctx=ast.Load(),
                                    ),
                                    attr="aquery",
                                    ctx=ast.Load(),
                                ),
                                keywords=[],
                                args=[generate_query_dict(o, client_schema, config)],
                            )
                        )
                    ),
                ],
                decorator_list=[],
                returns=ast.Name(id=o_name, ctx=ast.Load()),
            )
        )

    if plugin_config.generate_sync:
        tree.append(
            ast.FunctionDef(
                name=f"use{o.name.value}",
                args=generate_query_args(o, client_schema, config),
                body=[
                    generate_query_doc(o, client_schema, config),
                    ast.Return(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(
                                    id=o_name,
                                    ctx=ast.Load(),
                                ),
                                attr="query",
                                ctx=ast.Load(),
                            ),
                            keywords=[],
                            args=[generate_query_dict(o, client_schema, config)],
                        )
                    ),
                ],
                decorator_list=[],
                returns=ast.Name(id=o_name, ctx=ast.Load()),
            )
        )

    return tree


class OperationsFuncPlugin(Plugin):
    def __init__(self, config=None, **data):
        self.plugin_config = config or OperationsFuncPluginConfig(**data)

    def generate_body(
        self, client_schema: GraphQLSchema, config: GeneratorConfig
    ) -> List[ast.AST]:

        plugin_tree = []

        try:
            documents = parse_documents(
                client_schema, self.plugin_config.funcs_glob or config.documents
            )
        except NoDocumentsFoundError as e:
            logger.exception(e)
            return plugin_tree

        definitions = documents.definitions
        operations = [
            node for node in definitions if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            plugin_tree += generate_operation_func(
                operation, client_schema, config, self.plugin_config
            )

        return plugin_tree
