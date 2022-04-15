import glob
import re
from typing import Dict, List, Optional, Set, Union
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.language.ast import DocumentNode, FieldNode
from graphql.error.graphql_error import GraphQLError
from graphql import (
    BooleanValueNode,
    FloatValueNode,
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputType,
    GraphQLScalarType,
    IntValueNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    NullValueNode,
    OperationDefinitionNode,
    StringValueNode,
    ValueNode,
    VariableDefinitionNode,
    is_wrapping_type,
    parse,
    validate,
    build_client_schema,
    GraphQLInterfaceType,
)
import ast
from turms.registry import ClassRegistry
from turms.errors import (
    NoEnumFound,
    NoInputTypeFound,
    NoScalarFound,
    RegistryError,
)


class FragmentNotFoundError(Exception):
    pass


class NoDocumentsFoundError(Exception):
    pass


class NoScalarEquivalentDefined(Exception):
    pass


def target_from_node(node: FieldNode) -> str:
    return (
        node.alias.value if hasattr(node, "alias") and node.alias else node.name.value
    )


def generate_typename_field(typename, registry: ClassRegistry):

    registry.register_import("pydantic.Field")
    registry.register_import("typing.Optional")
    registry.register_import("typing.Literal")

    return ast.AnnAssign(
        target=ast.Name(id="typename", ctx=ast.Store()),
        annotation=ast.Subscript(
            value=ast.Name(id="Optional", ctx=ast.Load()),
            slice=ast.Subscript(
                value=ast.Name("Literal", ctx=ast.Load()),
                slice=ast.Constant(value=typename),
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        ),
        value=ast.Call(
            func=ast.Name(id="Field", ctx=ast.Load()),
            args=[],
            keywords=[ast.keyword(arg="alias", value=ast.Constant(value="__typename"))],
        ),
        simple=1,
    )


def generate_config_class(config: GeneratorConfig):

    config_fields = []

    if config.freeze:
        config_fields.append(
            ast.Assign(
                targets=[ast.Name(id="frozen", ctx=ast.Store())],
                value=ast.Constant(value=True),
            )
        )

    if len(config_fields) > 0:
        return [
            ast.ClassDef(
                name="Config",
                bases=[],
                keywords=[],
                body=config_fields,
                decorator_list=[],
            )
        ]
    else:
        return []


def parse_documents(
    client_schema: GraphQLSchema, scan_glob="g/*/**.graphql"
) -> DocumentNode:
    """ """

    x = glob.glob(scan_glob, recursive=True)

    errors: List[GraphQLError] = []

    dsl = ""

    for file in x:
        with open(file, "r") as f:
            dsl += f.read()

    if dsl == "":
        raise NoDocumentsFoundError(
            f"Glob {scan_glob} did not find documents. Or only empty documents"
        )

    nodes = parse(dsl)

    errors = validate(client_schema, nodes)
    if len(errors) > 0:
        raise Exception(errors)

    return nodes


fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


def replace_iteratively(
    pattern,
    registry,
    taken=[],
):
    z = set(fragment_searcher.findall(pattern))  # only set is important
    new_fragments = [new_f for new_f in z if new_f not in taken and new_f != ""]
    if not new_fragments:
        return pattern
    else:
        try:
            level_down_pattern = "\n\n".join(
                [registry.get_fragment_document(key) for key in new_fragments]
                + [pattern]
            )
            return replace_iteratively(
                level_down_pattern, registry, taken=new_fragments + taken
            )
        except KeyError as e:
            raise FragmentNotFoundError(
                f"Could not find in Fragment Map {registry}"
            ) from e


def get_additional_bases_for_type(
    typename, config: GeneratorConfig, registry: ClassRegistry
):

    if typename in config.additional_bases:
        for base in config.additional_bases[typename]:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in config.additional_bases[typename]
        ]
    return []


def get_interface_bases(config: GeneratorConfig, registry: ClassRegistry):

    if config.interface_bases:
        for base in config.interface_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in config.interface_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in config.object_bases
        ]


def interface_is_extended_by_other_interfaces(
    interface: GraphQLInterfaceType, other_interfaces: Set[GraphQLInterfaceType]
) -> bool:
    interfaces_implemented_by_other_interfaces = {
        nested_interface
        for other_interface in other_interfaces
        for nested_interface in other_interface.interfaces
    }
    return interface in interfaces_implemented_by_other_interfaces


def recurse_type_annotation(
    type: NamedTypeNode,
    registry: ClassRegistry,
    optional=True,
    overwrite_final: Optional[str] = None,
):

    if isinstance(type, NonNullTypeNode):
        return recurse_type_annotation(
            type.type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, ListTypeNode):
        if optional:
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name(id="List", ctx=ast.Load()),
                    slice=recurse_type_annotation(
                        type.type, registry, overwrite_final=overwrite_final
                    ),
                ),
            )

        return ast.Subscript(
            value=ast.Name(id="List", ctx=ast.Load()),
            slice=recurse_type_annotation(type.type, registry),
        )

    if isinstance(type, NamedTypeNode):
        if overwrite_final is not None:
            x = ast.Name(id=overwrite_final, ctx=ast.Load())
        else:
            try:
                x = registry.reference_scalar(type.name.value)
            except NoScalarFound:
                try:
                    x = registry.reference_inputtype(
                        type.name.value, "", allow_forward=False
                    )
                except NoInputTypeFound:
                    try:
                        x = registry.reference_enum(
                            type.name.value, "", allow_forward=False
                        )
                    except NoEnumFound:
                        raise NotImplementedError("Not implemented")

            if optional:
                return ast.Subscript(
                    value=ast.Name(id="Optional", ctx=ast.Load()),
                    slice=x,
                )

        return x


def recurse_type_label(
    type: NamedTypeNode,
    registry: ClassRegistry,
    optional=True,
    overwrite_final: Optional[str] = None,
):

    if isinstance(type, NonNullTypeNode):
        return recurse_type_annotation(
            type.type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, ListTypeNode):
        if optional:
            return (
                "Optional[List["
                + recurse_type_annotation(
                    type.type, registry, overwrite_final=overwrite_final
                )
                + "]]"
            )

        return (
            "List["
            + recurse_type_annotation(
                type.type, registry, overwrite_final=overwrite_final
            )
            + "]"
        )

    if isinstance(type, NamedTypeNode):
        if overwrite_final is not None:
            x = ast.Name(id=overwrite_final, ctx=ast.Load())
        else:
            try:
                x = registry.reference_scalar(type.name.value)
            except NoScalarFound:
                try:
                    x = registry.reference_inputtype(
                        type.name.value, "", allow_forward=False
                    )
                except NoInputTypeFound:
                    try:
                        x = registry.reference_enum(
                            type.name.value, "", allow_forward=False
                        )
                    except NoEnumFound:
                        raise NotImplementedError("Not implemented")

            if optional:
                return "Optional[" + x.id + "]"

        return x.id


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
