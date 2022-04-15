from __future__ import annotations

import ast
import logging
import re
from ctypes import Union
from enum import Enum
from typing import Any, List, Optional, Tuple

from graphql import (
    BooleanValueNode,
    FieldDefinitionNode,
    FloatValueNode,
    FragmentSpreadNode,
    GraphQLField,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLScalarType,
    IntValueNode,
    NamedTypeNode,
    NullValueNode,
    StringValueNode,
    ValueNode,
    VariableDefinitionNode,
)
from graphql.language.ast import (
    FieldNode,
    ListTypeNode,
    NonNullTypeNode,
    OperationDefinitionNode,
    OperationType,
)
from graphql.type.definition import GraphQLList
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.utilities.get_operation_root_type import get_operation_root_type
from graphql.utilities.type_info import get_field_def
from pydantic import BaseModel, Field
from turms.config import GeneratorConfig
from turms.errors import NoScalarEquivalentFound
from turms.plugins.base import Plugin, PluginConfig
from turms.registry import ClassRegistry
from turms.utils import NoDocumentsFoundError, parse_documents, target_from_node

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
    plugin_config: FuncsPluginConfig,
    config: GeneratorConfig,
    registry: ClassRegistry,
):

    return f"{plugin_config.prepend_async}{camel_to_snake(o.name.value)}"


def generate_sync_func_name(
    o: OperationDefinitionNode,
    plugin_config: FuncsPluginConfig,
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

            if optional:
                registry.register_import("typing.Optional")
                return ast.Subscript(
                    value=ast.Name(id="Optional", ctx=ast.Load()),
                    slice=ast.Name(
                        id=type_name,
                        ctx=ast.Load(),
                    ),
                    ctx=ast.Load(),
                )

            return ast.Name(
                id=type_name,
                ctx=ast.Load(),
            )

        except NoScalarEquivalentFound as e:

            if optional:
                registry.register_import("typing.Optional")
                return ast.Subscript(
                    value=ast.Name(id="Optional", ctx=ast.Load()),
                    slice=registry.reference_inputtype(
                        input_type.name.value, "", allow_forward=False
                    ),
                    ctx=ast.Load(),
                )

        return registry.reference_inputtype(
            input_type.name.value, "", allow_forward=False
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
                ctx=ast.Load(),
            )
        return ast.Subscript(
            value=ast.Name(id="List", ctx=ast.Load()),
            slice=get_input_type_annotation(input_type.type, config, registry),
            ctx=ast.Load(),
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
    plugin_config: FuncsPluginConfig,
) -> List[Arg]:

    args = plugin_config.global_args
    return args + definition.extra_args


def generate_passing_extra_args_for_onode(
    definition: FunctionDefinition, plugin_config: FuncsPluginConfig
):

    return [
        ast.Name(id=arg.key, ctx=ast.Load())
        for arg in get_extra_args_for_onode(definition, plugin_config)
    ]


def generate_passing_extra_kwargs_for_onode(
    definition: FunctionDefinition, plugin_config: FuncsPluginConfig
):

    return [
        ast.keyword(arg=kwarg.key, value=ast.Name(id=kwarg.key, ctx=ast.Load()))
        for kwarg in get_extra_kwargs_for_onode(definition, plugin_config)
    ]


def get_extra_kwargs_for_onode(
    definition: FunctionDefinition,
    plugin_config: FuncsPluginConfig,
) -> List[Kwarg]:

    kwargs = plugin_config.global_kwargs

    return kwargs + definition.extra_kwargs


def parse_value_node(value_node: ValueNode) -> Union[None, str, int, float, bool]:
    """Parses a Value Node into a Python value
    using standard types

    Args:
        value_node (ValueNode): The Argument Value Node

    Raises:
        NotImplementedError: If the Value Node is not supported

    Returns:
        Union[None, str, int, float, bool]: The parsed value
    """
    if isinstance(value_node, IntValueNode):
        return int(value_node.value)
    elif isinstance(value_node, FloatValueNode):
        return float(value_node.value)
    elif isinstance(value_node, StringValueNode):
        return value_node.value
    elif isinstance(value_node, BooleanValueNode):
        return value_node.value == "true"
    elif isinstance(value_node, NullValueNode):
        return None
    else:
        raise NotImplementedError(f"Cannot parse {value_node}")


def get_definitions_for_onode(
    operation_definition: OperationDefinitionNode,
    plugin_config: FuncsPluginConfig,
) -> List[Arg]:
    """Checks the Plugin Config if the operation definition should be included
    in the generated functions

    Args:
        operation_definition (OperationDefinitionNode): _description_
        plugin_config (FuncsPluginConfig): _description_

    Returns:
        List[Arg]: _description_
    """

    definitions = [
        definition
        for definition in plugin_config.definitions
        if definition.type == operation_definition.operation
    ]

    return definitions


def generate_query_args(
    definition: FunctionDefinition,
    operation_definition: OperationDefinitionNode,
    config: GeneratorConfig,
    plugin_config: FuncsPluginConfig,
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

    for v in operation_definition.variable_definitions:
        if isinstance(v.type, NonNullTypeNode) and not v.default_value:
            pos_args.append(
                ast.arg(
                    arg=registry.generate_parameter_name(v.variable.name.value),
                    annotation=get_input_type_annotation(v.type.type, config, registry),
                )
            )

    kw_args = []
    kw_values = []

    for v in operation_definition.variable_definitions:
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
        except NoScalarEquivalentFound:
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


def get_operation_class_name(o: OperationDefinitionNode, registry: ClassRegistry):

    if o.operation == OperationType.QUERY:
        o_name = registry.reference_query(o.name.value, "", allow_forward=False)
    if o.operation == OperationType.MUTATION:
        o_name = registry.reference_mutation(o.name.value, "", allow_forward=False)
    if o.operation == OperationType.SUBSCRIPTION:
        o_name = registry.reference_subscription(o.name.value, "", allow_forward=False)

    return o_name


class FieldModifier(str, Enum):
    OPTIONAL = "OPTIONAL"
    LIST = "LIST"


def formalize_type(
    field_definition: FieldDefinitionNode,
    registry: ClassRegistry,
    modifiers=None,
    next_is_optional=True,
):
    if modifiers is None:
        modifiers = []

    if isinstance(field_definition, GraphQLNonNull):
        return formalize_type(
            field_definition.of_type,
            registry,
            modifiers=modifiers,
            next_is_optional=False,
        )

    modifiers = modifiers + [FieldModifier.OPTIONAL] if next_is_optional else modifiers

    if isinstance(field_definition, GraphQLList):
        return formalize_type(
            field_definition.of_type,
            registry,
            modifiers=modifiers + [FieldModifier.LIST],
            next_is_optional=True,
        )

    if isinstance(field_definition, GraphQLScalarType):
        x = registry.get_scalar_equivalent(field_definition.name)
        return x, modifiers

    if isinstance(field_definition, GraphQLNamedType):

        try:
            x = registry.get_scalar_equivalent(field_definition.name)
        except NoScalarEquivalentFound as e:
            x = registry.get_inputtype_class(field_definition.name)

        return x, modifiers

    raise NotImplementedError(f"Cannot Handle this type of Node {field_definition}")


def build_type_annotation_for_field(
    field: GraphQLField, registry: ClassRegistry, overwrite_type: str = None
) -> ast.AST:
    """For a given field, build the type annotation for the field.

    This is used to build the type annotation for the field in the generated ast
    Graph. It first formalizes the type into the type.class and its modifiers
    as a list of Modifiers and then generates an annotation for this type


    Args:
        field (GraphQLField): The field to build the type annotation for
        registry (ClassRegistry): The class registry to use
        overwrite_type (str, optional): Overwrite the type. Defaults to None.

    Returns:
        ast.AST: The generated Annotation
    """

    end_type, modifiers = formalize_type(field.type, registry)
    end_type = overwrite_type if overwrite_type else end_type

    def recurse_annotate(modifiers):
        if len(modifiers) == 0:
            return ast.Name(id=end_type, ctx=ast.Load())
        else:
            this_modifier = modifiers[0]
            rest_modifiers = modifiers[1:]

            if this_modifier == FieldModifier.OPTIONAL:
                value = ast.Name(id="Optional", ctx=ast.Load())
            if this_modifier == FieldModifier.LIST:
                value = ast.Name(id="List", ctx=ast.Load())

            return ast.Subscript(
                value=value,
                slice=recurse_annotate(rest_modifiers),
                ctx=ast.Load(),
            )

    return recurse_annotate(modifiers)


def build_type_annotation_str_for_field(
    field: GraphQLField, registry: ClassRegistry, overwrite_type: str = None
) -> str:
    """For a given field, build the type annotation string for the field.

    This is used to build the type annotation for the field in the documentatoin

    Args:
        field (GraphQLField): The field to build the type annotation for
        registry (ClassRegistry): The class registry to use
        overwrite_type (str, optional): Overwrite the type. Defaults to None.

    Returns:
        str: The type anotation string
    """

    end_type, modifiers = formalize_type(field.type, registry)
    end_type = overwrite_type if overwrite_type else end_type

    def recurse_annotate(modifiers):
        if len(modifiers) == 0:
            return end_type
        else:
            this_modifier = modifiers[0]
            rest_modifiers = modifiers[1:]

            if this_modifier == FieldModifier.OPTIONAL:
                value = "Optional"
            if this_modifier == FieldModifier.LIST:
                value = "List"

            return f"{value}[{recurse_annotate(rest_modifiers)}]"

    return recurse_annotate(modifiers)


def get_return_type_annotation(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    registry: ClassRegistry,
    collapse: bool = True,
) -> Tuple[ast.AST, bool]:

    o_name = get_operation_class_name(o, registry)

    if len(o.selection_set.selections) == 0:
        raise NotImplementedError(
            "No operation specified. If you see this you probably didn't check the validities of your document."
        )

    root = get_operation_root_type(client_schema, o)

    if len(o.selection_set.selections) == 1 and collapse is True:
        potential_return_field = o.selection_set.selections[0]
        potential_return_type = get_field_def(
            client_schema, root, potential_return_field
        )

        if potential_return_field.selection_set is None:  # Dealing with a scalar type
            return (
                build_type_annotation_for_field(potential_return_type, registry),
                False,
            )

        if (
            len(potential_return_field.selection_set.selections) == 1
        ):  # Dealing with one Element
            if isinstance(
                potential_return_field.selection_set.selections[0], FragmentSpreadNode
            ):  # Dealing with a on element fragment
                return (
                    registry.reference_fragment(
                        potential_return_field.selection_set.selections[0].name.value,
                        "",
                        allow_forward=False,
                    ),
                    True,
                )
        # is a subseleciton of maybe multiple fragments or just a normal selection
        return (
            build_type_annotation_for_field(
                potential_return_type,
                registry,
                overwrite_type=f"{o_name}{o.selection_set.selections[0].name.value.capitalize()}",
            ),
            True,
        )

    return (
        ast.Name(
            id=o_name,
            ctx=ast.Load(),
        ),
        False,
    )


def get_return_type_string(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    registry: ClassRegistry,
    collapse=True,
) -> Tuple[str, bool]:

    o_name = get_operation_class_name(o, registry)

    if len(o.selection_set.selections) == 0:
        raise NotImplementedError(
            "No operation specified. If you see this you probably didn't check the validities of your document."
        )

    root = get_operation_root_type(client_schema, o)

    if len(o.selection_set.selections) == 1 and collapse == True:
        potential_return_field = o.selection_set.selections[0]
        potential_return_type = get_field_def(
            client_schema, root, potential_return_field
        )

        if potential_return_field.selection_set is None:  # Dealing with a scalar type
            return (
                build_type_annotation_str_for_field(potential_return_type, registry),
                False,
            )

        if (
            len(potential_return_field.selection_set.selections) == 1
        ):  # Dealing with one Element
            if isinstance(
                potential_return_field.selection_set.selections[0], FragmentSpreadNode
            ):  # Dealing with a on element fragment
                return (
                    registry.reference_fragment(
                        potential_return_field.selection_set.selections[0].name.value,
                        "",
                        allow_forward=False,
                    ),
                    True,
                )

            else:
                return (
                    build_type_annotation_str_for_field(
                        potential_return_type,
                        registry,
                        overwrite_type=f"{o_name}{o.selection_set.selections[0].name.value.capitalize()}",
                    ),
                    True,
                )

        else:
            return o_name, False

    else:
        return o_name, False


def generate_query_doc(
    definition: FunctionDefinition,
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: FuncsPluginConfig,
    registry: ClassRegistry,
    collapse=False,
):

    x = get_operation_root_type(client_schema, o)
    o.__annotations__

    o_name = get_operation_class_name(o, registry)

    return_type, collapsed = get_return_type_string(
        o, client_schema, registry, collapse
    )

    header = f"{o.name.value} \n\n"

    if collapsed:
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
    plugin_config: FuncsPluginConfig,
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
    plugin_config: FuncsPluginConfig,
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
    plugin_config: FuncsPluginConfig,
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
    plugin_config: FuncsPluginConfig,
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
    plugin_config: FuncsPluginConfig,
    registry: ClassRegistry,
):
    tree = []

    o_name = get_operation_class_name(o, registry)

    collapse = plugin_config.collapse_lonely

    returns, collapsed = get_return_type_annotation(
        o, client_schema, registry, collapse=collapse
    )

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
                    value=ast.Name(id="AsyncIterator", ctx=ast.Load()),
                    slice=returns,
                    ctx=ast.Load(),
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
                    value=ast.Name(id="Iterator", ctx=ast.Load()),
                    slice=returns,
                    ctx=ast.Load(),
                ),
            )
        )

    return tree


class FuncsPlugin(Plugin):
    config: FuncsPluginConfig = Field(default_factory=FuncsPluginConfig)

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
