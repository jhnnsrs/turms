from abc import abstractmethod
import ast
from typing import List

from graphql import FragmentSpreadNode, NamedTypeNode
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
    FieldNode,
    ListTypeNode,
    NonNullTypeNode,
    OperationDefinitionNode,
    OperationType,
)
from turms.registry import ClassRegistry
from turms.utils import (
    NoDocumentsFoundError,
    generate_typename_field,
    parse_documents,
    target_from_node,
)
from turms.errors import NoScalarEquivalentFound
import re
import ast

from graphql.type.definition import (
    GraphQLList,
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
    prepend_sync: str = ""
    prepend_async: str = "a"
    collapse_lonely: bool = True


def get_input_type_annotation(
    input_type: NamedTypeNode, config: GeneratorConfig, registry: ClassRegistry
):

    if isinstance(input_type, NamedTypeNode):

        try:
            type_name = registry.get_scalar_equivalent(input_type.name.value)
        except NoScalarEquivalentFound as e:
            type_name = registry.get_inputtype_class(input_type.name.value)

        print(type_name)
        return ast.Name(
            id=type_name,
            ctx=ast.Load(),
        )

    raise NotImplementedError()


def generate_query_args(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    registry: ClassRegistry,
):

    pos_args = []

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type.type, ListTypeNode):
                registry.register_import("typingl.List")
                pos_args.append(
                    ast.arg(
                        arg=v.variable.name.value,
                        annotation=ast.Subscript(
                            value=ast.Name("List", ctx=ast.Load()),
                            slice=get_input_type_annotation(
                                v.type.type, config, registry
                            ),
                        ),
                    )
                )
            else:
                registry.register_import("typing.List")
                pos_args.append(
                    ast.arg(
                        arg=v.variable.name.value,
                        annotation=get_input_type_annotation(
                            v.type.type, config, registry
                        ),
                    )
                )

    kw_args = []
    kw_values = []

    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type, ListTypeNode):
                registry.register_import("typing.List")
                kw_args.append(
                    ast.arg(
                        arg=v.variable.name.value,
                        annotation=ast.Subscript(
                            value=ast.Name("List", ctx=ast.Load()),
                            slice=get_input_type_annotation(
                                v.type.type, config, registry
                            ),
                        ),
                    )
                )
                kw_values.append(ast.Constant(value=None))
            else:
                kw_args.append(
                    ast.arg(
                        arg=v.variable.name.value,
                        annotation=get_input_type_annotation(v.type, config, registry),
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
            keys.append(ast.Constant(value=v.variable.name.value))
            values.append(ast.Name(id=v.variable.name.value, ctx=ast.Load()))

    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode):
            keys.append(ast.Constant(value=v.variable.name.value))
            values.append(ast.Name(id=v.variable.name.value, ctx=ast.Load()))

    return ast.Dict(keys=keys, values=values)


def generate_query_doc(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    registry: ClassRegistry,
    collapse=False,
):

    pos_args = []
    x = get_operation_root_type(client_schema, o)
    o.__annotations__

    if o.operation == OperationType.QUERY:
        o_name = registry.generate_query_classname(o.name.value)
    if o.operation == OperationType.MUTATION:
        o_name = registry.generate_mutation_classname(o.name.value)
    if o.operation == OperationType.SUBSCRIPTION:
        o_name = registry.generate_subscription_classname(o.name.value)

    if collapse:
        # Check if was collapsed from fragment

        return_type = f"{o_name}{o.selection_set.selections[0].name.value.capitalize()}"
        field_definition = get_field_def(
            client_schema, x, o.selection_set.selections[0]
        )

        potential_item = o.selection_set.selections[0]

        if potential_item.selection_set is None:
            return_type = registry.get_scalar_equivalent(field_definition.type.name)

        elif len(potential_item.selection_set.selections) == 1:
            if isinstance(
                potential_item.selection_set.selections[0], FragmentSpreadNode
            ):
                return_type = registry.get_fragment_class(
                    potential_item.selection_set.selections[0].name.value
                )

    else:

        return_type = f"{o_name}"

    header = f"{o.name.value} \n\n"

    if collapse:
        field = o.selection_set.selections[0]
        field_definition = get_field_def(client_schema, x, field)
        description = (
            header + field_definition.description
            if field_definition.description
            else header
        )

    else:
        query_descriptions = []

        for field in o.selection_set.selections:
            if isinstance(field, FieldNode):
                target = target_from_node(field)
                field_definition = get_field_def(client_schema, x, field)
                if field_definition.description:
                    query_descriptions.append(
                        f"{target}: {field_definition.description}"
                    )

        description = "\n ".join([header] + query_descriptions)

    description += "\n\nArguments:\n"

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type.type, ListTypeNode):
                description += f"    {v.variable.name.value} (List[{v.type.type.type.name.value}]): {v.type.type.type.name.value}\n"
            else:
                description += f"    {v.variable.name.value} ({v.type.type.name.value}): {v.type.type.name.value}\n"

    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode):
            if isinstance(v.type, ListTypeNode):
                description += f"    {v.variable.name.value} (List[{v.type.type.name.value}], Optional): {v.type.type.name.value}\n"
            else:
                description += f"    {v.variable.name.value} ({v.type.name.value}, Optional): {v.type.name.value}\n"

    description += "\nReturns:\n"
    description += f"    {return_type}: The returned Mutation\n"

    return ast.Expr(value=ast.Constant(value=description))


def genereate_async_call(o_name, o, client_schema, config, collapse):

    if not collapse:
        return ast.Return(
            value=ast.Await(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(
                            id=o_name,
                            ctx=ast.Load(),
                        ),
                        attr="aexecute",
                        ctx=ast.Load(),
                    ),
                    keywords=[],
                    args=[generate_query_dict(o, client_schema, config)],
                )
            )
        )
    else:
        return ast.Return(
            value=ast.Attribute(
                value=ast.Await(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(
                                id=o_name,
                                ctx=ast.Load(),
                            ),
                            attr="aexecute",
                            ctx=ast.Load(),
                        ),
                        keywords=[],
                        args=[generate_query_dict(o, client_schema, config)],
                    )
                ),
                attr=o.selection_set.selections[0].name.value,
                ctx=ast.Load(),
            )
        )


def genereate_sync_call(o_name, o, client_schema, config, collapse):

    if not collapse:
        return ast.Return(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(
                        id=o_name,
                        ctx=ast.Load(),
                    ),
                    attr="execute",
                    ctx=ast.Load(),
                ),
                keywords=[],
                args=[generate_query_dict(o, client_schema, config)],
            )
        )
    else:
        return ast.Return(
            value=ast.Attribute(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(
                            id=o_name,
                            ctx=ast.Load(),
                        ),
                        attr="execute",
                        ctx=ast.Load(),
                    ),
                    keywords=[],
                    args=[generate_query_dict(o, client_schema, config)],
                ),
                attr=o.selection_set.selections[0].name.value,
                ctx=ast.Load(),
            )
        )


def genereate_async_iterator(o_name, o, client_schema, config, collapse):

    if not collapse:
        return ast.AsyncFor(
            target=ast.Name(id="event", ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(
                        id=o_name,
                        ctx=ast.Load(),
                    ),
                    attr="asubscribe",
                    ctx=ast.Load(),
                ),
                args=[generate_query_dict(o, client_schema, config)],
                keywords=[],
            ),
            body=[
                ast.Expr(value=ast.Yield(value=ast.Name(id="event", ctx=ast.Load()))),
            ],
            orelse=[],
        )
    else:
        return ast.AsyncFor(
            target=ast.Name(id="event", ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(
                        id=o_name,
                        ctx=ast.Load(),
                    ),
                    attr="asubscribe",
                    ctx=ast.Load(),
                ),
                args=[generate_query_dict(o, client_schema, config)],
                keywords=[],
            ),
            body=[
                ast.Expr(
                    value=ast.Yield(
                        value=ast.Attribute(
                            value=ast.Name(id="event", ctx=ast.Load()),
                            ctx=ast.Load(),
                            attr=o.selection_set.selections[0].name.value,
                        )
                    )
                ),
            ],
            orelse=[],
        )


def genereate_sync_iterator(o_name, o, client_schema, config, collapse):

    if not collapse:
        return ast.For(
            target=ast.Name(id="event", ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(
                        id=o_name,
                        ctx=ast.Load(),
                    ),
                    attr="subscribe",
                    ctx=ast.Load(),
                ),
                args=[generate_query_dict(o, client_schema, config)],
                keywords=[],
            ),
            body=[
                ast.Expr(value=ast.Yield(value=ast.Name(id="event", ctx=ast.Load()))),
            ],
            orelse=[],
        )
    else:
        return ast.For(
            target=ast.Name(id="event", ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(
                        id=o_name,
                        ctx=ast.Load(),
                    ),
                    attr="subscribe",
                    ctx=ast.Load(),
                ),
                args=[generate_query_dict(o, client_schema, config)],
                keywords=[],
            ),
            body=[
                ast.Expr(
                    value=ast.Yield(
                        value=ast.Attribute(
                            value=ast.Name(id="event", ctx=ast.Load()),
                            ctx=ast.Load(),
                            attr=o.selection_set.selections[0].name.value,
                        )
                    )
                ),
            ],
            orelse=[],
        )


def generate_operation_func(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
):
    tree = []

    if o.operation == OperationType.QUERY:
        o_name = registry.generate_query_classname(o.name.value)
    if o.operation == OperationType.MUTATION:
        o_name = registry.generate_mutation_classname(o.name.value)
    if o.operation == OperationType.SUBSCRIPTION:
        o_name = registry.generate_subscription_classname(o.name.value)

    collapse = len(o.selection_set.selections) == 1 and plugin_config.collapse_lonely

    return_type = (
        f"{o_name}{o.selection_set.selections[0].name.value.capitalize()}"
        if collapse
        else o_name
    )

    if collapse:
        x = get_operation_root_type(client_schema, o)
        field_definition = get_field_def(
            client_schema, x, o.selection_set.selections[0]
        )

        potential_item = o.selection_set.selections[0]

        # Check if was collapsed from fragment
        if potential_item.selection_set is None:
            return_type = registry.get_scalar_equivalent(field_definition.type.name)

        elif len(potential_item.selection_set.selections) == 1:
            if isinstance(
                potential_item.selection_set.selections[0], FragmentSpreadNode
            ):
                return_type = registry.get_fragment_class(
                    potential_item.selection_set.selections[0].name.value
                )
        else:
            return_type = (
                f"{o_name}{o.selection_set.selections[0].name.value.capitalize()}"
            )

        if isinstance(field_definition.type, GraphQLList):
            returns = ast.Subscript(
                value=ast.Name(id="List", ctx=ast.Load()),
                slice=ast.Name(id=return_type, ctx=ast.Load()),
            )
        else:
            returns = ast.Name(id=return_type, ctx=ast.Load())
    else:
        returns = ast.Name(id=return_type, ctx=ast.Load())

    doc = generate_query_doc(o, client_schema, config, registry, collapse=collapse)

    if plugin_config.generate_async:
        tree.append(
            ast.AsyncFunctionDef(
                name=f"{plugin_config.prepend_async}{o.name.value}",
                args=generate_query_args(o, client_schema, config, registry),
                body=[
                    doc,
                    genereate_async_call(o_name, o, client_schema, config, collapse)
                    if o.operation != OperationType.SUBSCRIPTION
                    else genereate_async_iterator(
                        o_name, o, client_schema, config, collapse
                    ),
                ],
                decorator_list=[],
                returns=returns,
            )
        )

    if plugin_config.generate_sync:
        tree.append(
            ast.FunctionDef(
                name=f"{plugin_config.prepend_sync}{o.name.value}",
                args=generate_query_args(o, client_schema, config, registry),
                body=[
                    doc,
                    genereate_sync_call(o_name, o, client_schema, config, collapse)
                    if o.operation != OperationType.SUBSCRIPTION
                    else genereate_sync_iterator(
                        o_name, o, client_schema, config, collapse
                    ),
                ],
                decorator_list=[],
                returns=returns,
            )
        )

    return tree


class OperationsFuncPlugin(Plugin):
    def __init__(self, config=None, **data):
        self.plugin_config = config or OperationsFuncPluginConfig(**data)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
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
                operation, client_schema, config, self.plugin_config, registry
            )

        return plugin_tree
