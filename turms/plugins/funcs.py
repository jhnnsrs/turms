from __future__ import annotations
from abc import abstractmethod
import ast
from typing import Any, List, Literal
from attr import Attribute

from graphql import (
    BooleanValueNode,
    FloatValueNode,
    FragmentSpreadNode,
    GraphQLNonNull,
    IntValueNode,
    NamedTypeNode,
    NullValueNode,
    StringValueNode,
    ValueNode,
    VariableDefinitionNode,
)
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin, PluginConfig
from pydantic import BaseModel, BaseSettings, Field
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
from typing import Optional, Union


logger = logging.getLogger(__name__)


class Kwarg(BaseModel):
    key: str
    type: str
    description: str = "Specify that in turms.plugin.funcs.OperationsFuncPlugin"
    default: Any = None


class Arg(BaseModel):
    key: str
    type: str
    description: str = "Specify that in turms.plugin.funcs.OperationsFuncPlugin"


class FunctionDefinition(BaseModel):
    type: OperationType
    is_async: bool = False
    extra_args: List[Arg] = []
    extra_kwargs: List[Kwarg] = []
    use: str


class FuncsPluginConfig(PluginConfig):
    type = "turms.plugins.funcs.FuncsPlugin"
    funcs_glob: Optional[str]
    prepend_sync: str = ""
    prepend_async: str = "a"
    collapse_lonely: bool = True
    global_args: List[Arg] = []
    global_kwargs: List[Kwarg] = []
    definitions: List[FunctionDefinition] = []

    class Config:
        env_prefix = "TURMS_PLUGINS_FUNCS_"


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def generate_async_func_name(
    o: OperationDefinitionNode,
    plugin_config: OperationsFuncPluginConfig,
    config: GeneratorConfig,
    registry: ClassRegistry,
):

    return f"{plugin_config.prepend_async}{camel_to_snake(o.name.value)}"


def generate_sync_func_name(
    o: OperationDefinitionNode,
    plugin_config: OperationsFuncPluginConfig,
    config: GeneratorConfig,
    registry: ClassRegistry,
):

    return f"{plugin_config.prepend_sync}{camel_to_snake(o.name.value)}"


def get_input_type_annotation(
    input_type: NamedTypeNode,
    config: GeneratorConfig,
    registry: ClassRegistry,
    optional=True,
):

    if isinstance(input_type, NamedTypeNode):
        try:
            type_name = registry.get_scalar_equivalent(input_type.name.value)
        except NoScalarEquivalentFound as e:
            type_name = registry.get_inputtype_class(input_type.name.value)

        if optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=ast.Name(
                    id=type_name,
                    ctx=ast.Load(),
                ),
            )

        return ast.Name(
            id=type_name,
            ctx=ast.Load(),
        )

    elif isinstance(input_type, ListTypeNode):
        registry.register_import("typing.List")

        if optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name(id="List", ctx=ast.Load()),
                    slice=get_input_type_annotation(input_type.type, config, registry),
                ),
            )
        return ast.Subscript(
            value=ast.Name(id="List", ctx=ast.Load()),
            slice=get_input_type_annotation(input_type.type, config, registry),
        )

    elif isinstance(input_type, NonNullTypeNode):
        return get_input_type_annotation(
            input_type.type, config, registry, optional=False
        )

    raise NotImplementedError()


wanted_definition = {
    OperationType.MUTATION: {
        "async": "asyncfunction",
        "sync": "function",
    },
    OperationType.QUERY: {
        "async": "asyncfunction",
        "sync": "function",
    },
    OperationType.SUBSCRIPTION: {
        "async": "asynciterator",
        "sync": "iterator",
    },
}


def get_extra_args_for_onode(
    definition: FunctionDefinition,
    plugin_config: OperationsFuncPluginConfig,
) -> List[Arg]:

    args = plugin_config.global_args
    return args + definition.extra_args


def generate_passing_extra_args_for_onode(
    definition: FunctionDefinition, plugin_config: OperationsFuncPluginConfig
):

    return [
        ast.Name(id=arg.key, ctx=ast.Load())
        for arg in get_extra_args_for_onode(definition, plugin_config)
    ]


def generate_passing_extra_kwargs_for_onode(
    definition: FunctionDefinition, plugin_config: OperationsFuncPluginConfig
):

    return [
        ast.keyword(arg=kwarg.key, value=ast.Name(id=kwarg.key, ctx=ast.Load()))
        for kwarg in get_extra_kwargs_for_onode(definition, plugin_config)
    ]


def get_extra_kwargs_for_onode(
    definition: FunctionDefinition,
    plugin_config: OperationsFuncPluginConfig,
) -> List[Arg]:

    kwargs = plugin_config.global_kwargs

    return kwargs + definition.extra_kwargs


def parse_value_node(x: ValueNode):
    if isinstance(x, IntValueNode):
        return int(x.value)
    elif isinstance(x, FloatValueNode):
        return float(x.value)
    elif isinstance(x, StringValueNode):
        return x.value
    elif isinstance(x, BooleanValueNode):
        return x.value == "true"
    elif isinstance(x, NullValueNode):
        return None
    else:
        raise NotImplementedError(f"cannot parse {x}")


def get_definitions_for_onode(
    o: OperationDefinitionNode,
    plugin_config: OperationsFuncPluginConfig,
) -> List[Arg]:

    definitions = [
        definition
        for definition in plugin_config.definitions
        if definition.type == o.operation
    ]

    return definitions


def generate_query_args(
    definition: FunctionDefinition,
    o: OperationDefinitionNode,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
):

    extra_args = get_extra_args_for_onode(definition, plugin_config)
    pos_args = []

    for arg in extra_args:
        registry.register_import(arg.type)
        pos_args.append(
            ast.arg(
                arg=arg.key,
                annotation=ast.Name(
                    id=arg.type.split(".")[-1],
                    ctx=ast.Load(),
                ),
            )
        )

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode) and not v.default_value:
            pos_args.append(
                ast.arg(
                    arg=registry.generate_parameter_name(v.variable.name.value),
                    annotation=get_input_type_annotation(v.type.type, config, registry),
                )
            )

    kw_args = []
    kw_values = []

    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode) or v.default_value:
            kw_args.append(
                ast.arg(
                    arg=registry.generate_parameter_name(v.variable.name.value),
                    annotation=get_input_type_annotation(v.type, config, registry),
                )
            )
            kw_values.append(
                ast.Constant(
                    value=parse_value_node(v.default_value) if v.default_value else None
                )
            )

    extra_kwargs = get_extra_kwargs_for_onode(definition, plugin_config)

    for kwarg in extra_kwargs:
        registry.register_import(kwarg.type)
        kw_args.append(
            ast.arg(
                arg=kwarg.key,
                annotation=ast.Name(
                    id=kwarg.type.split(".")[-1],
                    ctx=ast.Load(),
                ),
            )
        )
        kw_values.append(ast.Constant(value=kwarg.default))

    return ast.arguments(
        args=pos_args + kw_args,
        posonlyargs=[],
        kwonlyargs=[],
        kw_defaults=[],
        defaults=kw_values,
    )


def generate_query_dict(o: OperationDefinitionNode, registry: ClassRegistry):

    keys = []
    values = []

    for v in o.variable_definitions:
        keys.append(ast.Constant(value=v.variable.name.value))
        values.append(
            ast.Name(
                id=registry.generate_parameter_name(v.variable.name.value),
                ctx=ast.Load(),
            )
        )

    return ast.Dict(keys=keys, values=values)


def generate_document_arg(o_name):

    return ast.Name(id=o_name, ctx=ast.Load())


def recurse_variable_annotation(
    v: VariableDefinitionNode, registry: ClassRegistry, optional=True
):

    if isinstance(v.type, NamedTypeNode):
        try:
            x = registry.get_scalar_equivalent(v.type.name.value)
        except NoScalarEquivalentFound as e:
            x = registry.get_inputtype_class(v.type.name.value)
        if optional:
            return "Optional[" + x + "]"
        else:
            return x

    elif isinstance(v.type, NonNullTypeNode):
        return recurse_variable_annotation(v.type, registry, optional=False)

    elif isinstance(v.type, ListTypeNode):
        if optional:
            return (
                "Optional[List[" + recurse_variable_annotation(v.type, registry) + "]]"
            )
        return "List[" + recurse_variable_annotation(v.type, registry) + "]"

    raise NotImplementedError()


def generate_query_doc(
    definition: FunctionDefinition,
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
    collapse=False,
):

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

    extra_args = get_extra_args_for_onode(definition, plugin_config)

    for arg in extra_args:
        description += f"    {arg.key} ({arg.type}): {arg.description}\n"

    for v in o.variable_definitions:
        if isinstance(v.type, NonNullTypeNode) and not v.default_value:
            description += f"    {registry.generate_parameter_name(v.variable.name.value)} ({recurse_variable_annotation(v, registry)}): {v.variable.name.value}\n"

    for v in o.variable_definitions:
        if not isinstance(v.type, NonNullTypeNode) or v.default_value:
            description += f"    {registry.generate_parameter_name(v.variable.name.value)} ({recurse_variable_annotation(v, registry)}, optional): {v.variable.name.value}. {'' if not v.default_value else  'Defaults to ' + str(v.default_value.value)}\n"

    extra_kwargs = get_extra_kwargs_for_onode(definition, plugin_config)
    for kwarg in extra_kwargs:
        description += (
            f"    {kwarg.key} ({kwarg.type}, optional): {kwarg.description}\n"
        )

    description += "\nReturns:\n"
    description += f"    {return_type}"

    return ast.Expr(value=ast.Constant(value=description))


def genereate_async_call(
    definition: FunctionDefinition,
    o_name: str,
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
    collapse=False,
):
    registry.register_import(definition.use)
    if not collapse:
        return ast.Return(
            value=ast.Await(
                value=ast.Call(
                    func=ast.Name(
                        id=definition.use.split(".")[-1],
                        ctx=ast.Load(),
                    ),
                    keywords=generate_passing_extra_kwargs_for_onode(
                        definition, plugin_config
                    ),
                    args=generate_passing_extra_args_for_onode(
                        definition, plugin_config
                    )
                    + [
                        generate_document_arg(o_name),
                        generate_query_dict(o, registry),
                    ],
                )
            )
        )
    else:

        return ast.Return(
            value=ast.Attribute(
                value=ast.Await(
                    value=ast.Call(
                        func=ast.Name(
                            id=definition.use.split(".")[-1],
                            ctx=ast.Load(),
                        ),
                        keywords=generate_passing_extra_kwargs_for_onode(
                            definition, plugin_config
                        ),
                        args=generate_passing_extra_args_for_onode(
                            definition, plugin_config
                        )
                        + [
                            generate_document_arg(o_name),
                            generate_query_dict(o, registry),
                        ],
                    )
                ),
                attr=registry.generate_node_name(
                    o.selection_set.selections[0].name.value
                ),
                ctx=ast.Load(),
            )
        )


def genereate_sync_call(
    definition: FunctionDefinition,
    o_name: str,
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
    collapse=False,
):
    registry.register_import(definition.use)
    if not collapse:
        return ast.Return(
            value=ast.Call(
                func=ast.Name(
                    id=definition.use.split(".")[-1],
                    ctx=ast.Load(),
                ),
                keywords=generate_passing_extra_kwargs_for_onode(
                    definition, plugin_config
                ),
                args=generate_passing_extra_args_for_onode(definition, plugin_config)
                + [
                    generate_document_arg(o_name),
                    generate_query_dict(o, registry),
                ],
            )
        )
    else:
        return ast.Return(
            value=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(
                        id=definition.use.split(".")[-1],
                        ctx=ast.Load(),
                    ),
                    keywords=generate_passing_extra_kwargs_for_onode(
                        definition, plugin_config
                    ),
                    args=generate_passing_extra_args_for_onode(
                        definition, plugin_config
                    )
                    + [
                        generate_document_arg(o_name),
                        generate_query_dict(o, registry),
                    ],
                ),
                attr=registry.generate_node_name(
                    o.selection_set.selections[0].name.value
                ),
                ctx=ast.Load(),
            )
        )


def genereate_async_iterator(
    definition: FunctionDefinition,
    o_name: str,
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
    collapse=False,
):
    registry.register_import(definition.use)
    if not collapse:
        return ast.AsyncFor(
            target=ast.Name(id="event", ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Name(
                    id=definition.use.split(".")[-1],
                    ctx=ast.Load(),
                ),
                keywords=generate_passing_extra_kwargs_for_onode(
                    definition, plugin_config
                ),
                args=generate_passing_extra_args_for_onode(definition, plugin_config)
                + [
                    generate_document_arg(o_name),
                    generate_query_dict(o, registry),
                ],
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
                func=ast.Name(
                    id=definition.use.split(".")[-1],
                    ctx=ast.Load(),
                ),
                keywords=generate_passing_extra_kwargs_for_onode(
                    definition, plugin_config
                ),
                args=generate_passing_extra_args_for_onode(definition, plugin_config)
                + [
                    generate_document_arg(o_name),
                    generate_query_dict(o, registry),
                ],
            ),
            body=[
                ast.Expr(
                    value=ast.Yield(
                        value=ast.Attribute(
                            value=ast.Name(id="event", ctx=ast.Load()),
                            ctx=ast.Load(),
                            attr=registry.generate_node_name(
                                o.selection_set.selections[0].name.value
                            ),
                        )
                    )
                ),
            ],
            orelse=[],
        )


def genereate_sync_iterator(
    definition: FunctionDefinition,
    o_name: str,
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsFuncPluginConfig,
    registry: ClassRegistry,
    collapse=False,
):
    registry.register_import(definition.use)
    if not collapse:
        return ast.For(
            target=ast.Name(id="event", ctx=ast.Store()),
            iter=ast.Call(
                func=ast.Name(
                    id=definition.use.split(".")[-1],
                    ctx=ast.Load(),
                ),
                keywords=generate_passing_extra_kwargs_for_onode(
                    definition, plugin_config
                ),
                args=generate_passing_extra_args_for_onode(definition, plugin_config)
                + [
                    generate_document_arg(o_name),
                    generate_query_dict(o, registry),
                ],
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
                func=ast.Name(
                    id=definition.use.split(".")[-1],
                    ctx=ast.Load(),
                ),
                keywords=generate_passing_extra_kwargs_for_onode(
                    definition, plugin_config
                ),
                args=generate_passing_extra_args_for_onode(definition, plugin_config)
                + [
                    generate_document_arg(o_name),
                    generate_query_dict(o, registry),
                ],
            ),
            body=[
                ast.Expr(
                    value=ast.Yield(
                        value=ast.Attribute(
                            value=ast.Name(id="event", ctx=ast.Load()),
                            ctx=ast.Load(),
                            attr=registry.generate_node_name(
                                o.selection_set.selections[0].name.value
                            ),
                        )
                    )
                ),
            ],
            orelse=[],
        )


def generate_operation_func(
    definition: FunctionDefinition,
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

        if isinstance(field_definition.type, GraphQLNonNull):
            if isinstance(field_definition.type.of_type, GraphQLList):
                returns = ast.Subscript(
                    value=ast.Name(id="List", ctx=ast.Load()),
                    slice=ast.Name(id=return_type, ctx=ast.Load()),
                )
            else:
                returns = ast.Name(id=return_type, ctx=ast.Load())
        else:
            if isinstance(field_definition.type, GraphQLList):
                returns = ast.Subscript(
                    value=ast.Name("Optional", ctx=ast.Load()),
                    slice=ast.Subscript(
                        value=ast.Name(id="List", ctx=ast.Load()),
                        slice=ast.Name(id=return_type, ctx=ast.Load()),
                    ),
                )
            else:
                returns = ast.Subscript(
                    value=ast.Name("Optional", ctx=ast.Load()),
                    slice=ast.Name(id=return_type, ctx=ast.Load()),
                )
    else:
        returns = ast.Name(id=return_type, ctx=ast.Load())

    doc = generate_query_doc(
        definition, o, client_schema, config, plugin_config, registry, collapse
    )

    if definition.is_async:
        if o.operation == OperationType.SUBSCRIPTION:
            registry.register_import("typing.AsyncIterator")

        tree.append(
            ast.AsyncFunctionDef(
                name=generate_async_func_name(o, plugin_config, config, registry),
                args=generate_query_args(
                    definition,
                    o,
                    config,
                    plugin_config,
                    registry,
                ),
                body=[
                    doc,
                    genereate_async_call(
                        definition,
                        o_name,
                        o,
                        client_schema,
                        config,
                        plugin_config,
                        registry,
                        collapse,
                    )
                    if definition.type != OperationType.SUBSCRIPTION
                    else genereate_async_iterator(
                        definition,
                        o_name,
                        o,
                        client_schema,
                        config,
                        plugin_config,
                        registry,
                        collapse,
                    ),
                ],
                decorator_list=[],
                returns=returns
                if definition.type != OperationType.SUBSCRIPTION
                else ast.Subscript(
                    value=ast.Name(id="AsyncIterator", ctx=ast.Load()), slice=returns
                ),
            )
        )

    if not definition.is_async:
        if o.operation == OperationType.SUBSCRIPTION:
            registry.register_import("typing.Iterator")

        tree.append(
            ast.FunctionDef(
                name=generate_sync_func_name(o, plugin_config, config, registry),
                args=generate_query_args(
                    definition,
                    o,
                    config,
                    plugin_config,
                    registry,
                ),
                body=[
                    doc,
                    genereate_sync_call(
                        definition,
                        o_name,
                        o,
                        client_schema,
                        config,
                        plugin_config,
                        registry,
                        collapse,
                    )
                    if definition.type != OperationType.SUBSCRIPTION
                    else genereate_sync_iterator(
                        definition,
                        o_name,
                        o,
                        client_schema,
                        config,
                        plugin_config,
                        registry,
                        collapse,
                    ),
                ],
                decorator_list=[],
                returns=returns
                if definition.type != OperationType.SUBSCRIPTION
                else ast.Subscript(
                    value=ast.Name(id="Iterator", ctx=ast.Load()), slice=returns
                ),
            )
        )

    return tree


class FuncsPlugin(Plugin):
    config: FuncsPluginConfig = Field(default_facotry=FuncsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        plugin_tree = []

        try:
            documents = parse_documents(
                client_schema, self.config.funcs_glob or config.documents
            )
        except NoDocumentsFoundError as e:
            logger.exception(e)
            return plugin_tree

        operations = [
            node
            for node in documents.definitions
            if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            for definition in get_definitions_for_onode(operation, self.config):
                plugin_tree += generate_operation_func(
                    definition,
                    operation,
                    client_schema,
                    config,
                    self.config,
                    registry,
                )

        return plugin_tree
