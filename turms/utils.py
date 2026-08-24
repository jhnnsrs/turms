import ast
import glob
import re
from typing import List, Optional, Sequence, Set, Union

from graphql import (
    BooleanValueNode,
    FloatValueNode,
    FragmentDefinitionNode,
    GraphQLEnumType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedOutputType,
    GraphQLNonNull,
    GraphQLNullableType,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLUnionType,
    IntValueNode,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    NullValueNode,
    OperationDefinitionNode,
    SelectionNode,
    SelectionSetNode,
    StringValueNode,
    TypeNode,
    Undefined,
    ValueNode,
    parse,
    print_ast,
    validate,
)
from graphql.error.graphql_error import GraphQLError
from graphql.language.ast import DocumentNode, FieldNode, NameNode
from graphql import GraphQLSchema

from turms.annotations import list_label, optional_label
from turms.config import GeneratorConfig
from turms.errors import (
    GenerationError,
    NoEnumFound,
    NoInputTypeFound,
    NoScalarFound,
)
from turms.registry import ClassRegistry

from .config import GraphQLTypes

commentline_regex = re.compile(r"^.*#(.*)")
#: A line that is *only* a comment. Used to walk back over the block of `#` lines above an
#: operation: graphql-core puts the operation's `loc.start` on the last of them, so slicing
#: forward from there would keep that line alone and drop the rest of the block.
comment_only_regex = re.compile(r"^\s*#")


class FragmentNotFoundError(GenerationError):
    pass


class NoDocumentsFoundError(GenerationError):
    pass


class InvalidDocuments(GenerationError):
    pass


class NoScalarEquivalentDefined(GenerationError):
    pass


def merge_body_sequences(
    *sequences: Sequence[
        ast.AnnAssign | ast.Assign | ast.Expr | ast.ClassDef | ast.Pass
    ],
) -> list[ast.stmt]:
    """Merges a list of sequences into a single sequence"""
    merged: list[ast.stmt] = []
    for seq in sequences:
        merged.extend(seq)
    return merged


def merge_bases_sequences(
    *sequences: Sequence[ast.Name],
) -> list[ast.expr]:
    """Merges a list of sequences into a single sequence"""
    merged = []
    for seq in sequences:
        merged.extend(seq)  # type: ignore
    return merged  # type: ignore


def target_from_node(node: FieldNode) -> str:
    """Extacts the field name from a FieldNode. If alias is present, it will be used instead of the name"""
    return (
        node.alias.value if hasattr(node, "alias") and node.alias else node.name.value
    )


def non_typename_fields(
    node: FieldNode | FragmentDefinitionNode,
) -> List[FieldNode | SelectionNode]:
    """Returns all fields in a FieldNode that are not __typename"""
    if not node.selection_set:
        return []
    return [
        field
        for field in node.selection_set.selections
        if not (isinstance(field, FieldNode) and field.name.value == "__typename")
    ]


def inspect_operation_for_documentation(operation: OperationDefinitionNode):
    """Checks for operation level documentatoin"""

    if not operation.loc:
        raise GenerationError(
            "Could not find loc for operation. This should not happen"
        )

    if not operation.selection_set:
        raise GenerationError(
            "Could not find selection set for operation. This should not happen"
        )

    first_operation = operation.selection_set.selections[0]
    if not first_operation.loc:
        raise GenerationError(
            "Could not find loc for first operation. This should not happen"
        )

    lines = operation.loc.source.body.splitlines()
    end = operation.loc.source.get_location(first_operation.loc.start).line - 1
    start = operation.loc.source.get_location(operation.loc.start).line - 1

    # Comments *above* the operation are part of its documentation, but `loc.start` lands on
    # the last comment token rather than on the `query`/`mutation` keyword, so starting there
    # keeps only the block's final line. Walk back over the contiguous block instead. Any
    # non-comment line stops the walk -- a blank line, or the previous operation's closing
    # brace -- so a neighbouring block can never be absorbed into this one.
    while start > 0 and comment_only_regex.match(lines[start - 1]):
        start -= 1

    definition = lines[start:end]
    doc: list[str] = []
    for line in definition:
        if line and line != "":
            x = commentline_regex.match(line)
            if x:
                doc.append(x.group(1))

    return "\n".join(doc) if doc else None


def generate_typename_field(
    typename: str, registry: ClassRegistry, config: GeneratorConfig
):
    """Generates the typename field a specific type, this will be used to determine the type of the object in the response"""

    registry.register_import("pydantic.Field")
    registry.register_import("typing.Optional")
    registry.register_import("typing.Literal")

    keywords = [
        ast.keyword(arg="alias", value=ast.Constant(value="__typename")),
        ast.keyword(arg="default", value=ast.Constant(value=typename)),
    ]
    if config.exclude_typenames:
        keywords.append(ast.keyword(arg="exclude", value=ast.Constant(value=True)))

    return ast.AnnAssign(
        target=ast.Name(id="typename", ctx=ast.Store()),
        annotation=ast.Subscript(
            value=ast.Name("Literal", ctx=ast.Load()),
            slice=ast.Constant(value=typename),
            ctx=ast.Load(),
        ),
        value=ast.Call(
            func=ast.Name(id="Field", ctx=ast.Load()),
            args=[],
            keywords=keywords,
        ),
        simple=1,
    )


def generate_alias_keywords(
    field_name: str,
    graphql_name: str,
    config: GeneratorConfig,
    registry: ClassRegistry,
) -> List[ast.keyword]:
    """The ``Field(...)`` keywords that carry a field's GraphQL name.

    Only called when the python name and the GraphQL name actually differ.

    Under ``alias_mode="split"`` the single ``alias=`` becomes a
    ``validation_alias``/``serialization_alias`` pair. Both spellings still
    validate (the python name is the first ``AliasChoices`` entry) and
    ``model_dump(by_alias=True)`` still emits the GraphQL name, so the wire
    format is unchanged -- but with no ``alias=`` field specifier present, a type
    checker synthesizes ``__init__`` from the python name instead of the GraphQL
    one. That is the whole point: ``populate_by_name`` is a runtime-only setting
    that type checkers do not read, so under ``"single"`` the snake_case spelling
    works but does not type-check.

    Never use this for a discriminated-union tag field: pydantic rejects a
    non-string alias on one ("Alias [...] is not supported in a discriminated
    union"). Tag fields carry no alias at all, so they never reach this helper.
    """
    if config.options.alias_mode == "split":
        registry.register_import("pydantic.AliasChoices")
        return [
            ast.keyword(
                arg="validation_alias",
                value=ast.Call(
                    func=ast.Name(id="AliasChoices", ctx=ast.Load()),
                    args=[
                        ast.Constant(value=field_name),
                        ast.Constant(value=graphql_name),
                    ],
                    keywords=[],
                ),
            ),
            ast.keyword(
                arg="serialization_alias", value=ast.Constant(value=graphql_name)
            ),
        ]

    return [ast.keyword(arg="alias", value=ast.Constant(value=graphql_name))]


def generate_generic_typename_field(registry: ClassRegistry, config: GeneratorConfig):
    """Generates the typename field a specific type, this will be used to determine the type of the object in the response"""

    registry.register_import("pydantic.Field")
    registry.register_import("typing.Optional")
    registry.register_import("typing.Literal")

    keywords = [
        ast.keyword(arg="alias", value=ast.Constant(value="__typename")),
    ]
    if config.exclude_typenames:
        keywords.append(ast.keyword(arg="exclude", value=ast.Constant(value=True)))

    return ast.AnnAssign(
        target=ast.Name(id="typename", ctx=ast.Store()),
        annotation=ast.Name("str", ctx=ast.Load()),
        value=ast.Call(
            func=ast.Name(id="Field", ctx=ast.Load()),
            args=[],
            keywords=keywords,
        ),
        simple=1,
    )


def generate_pydantic_config(
    graphQLType: GraphQLTypes,
    config: GeneratorConfig,
    registry: ClassRegistry,
    typename: Optional[str] = None,
) -> list[ast.Assign]:
    """Generates the ``model_config`` assignment for a specific type

    It will append the config class to the registry, and set the frozen
    attribute for the class to True, if the freeze config is enabled and
    the type appears in the freeze list.

    It will also add config attributes to the class, if the type appears in
    'additional_config' in the config file.

    """

    config_keywords: List[ast.keyword] = []

    if config.freeze.enabled:
        if graphQLType in config.freeze.types:
            if config.freeze.exclude and typename in config.freeze.exclude:
                pass
            elif config.freeze.include and typename not in config.freeze.include:
                pass
            else:
                config_keywords.append(
                    ast.keyword(arg="frozen", value=ast.Constant(value=True))
                )

    if config.options.enabled:
        if graphQLType in config.options.types:
            if config.options.exclude and typename in config.options.exclude:
                pass
            elif config.options.include and typename not in config.options.include:
                pass
            else:
                if config.options.extra is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="extra", value=ast.Constant(value=config.options.extra)
                        )
                    )

                if config.options.validate_assignment is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="validate_assignment",
                            value=ast.Constant(
                                value=config.options.validate_assignment
                            ),
                        )
                    )

                if config.options.allow_population_by_field_name is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="populate_by_name",
                            value=ast.Constant(
                                value=config.options.allow_population_by_field_name
                            ),
                        )
                    )

                if config.options.from_attributes is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="from_attributes",
                            value=ast.Constant(
                                value=config.options.from_attributes
                            ),
                        )
                    )

                if config.options.use_enum_values is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="use_enum_values",
                            value=ast.Constant(value=config.options.use_enum_values),
                        )
                    )

    if typename:
        if typename in config.additional_config:
            for key, value in config.additional_config[typename].items():
                config_keywords.append(
                    ast.keyword(arg=key, value=ast.Constant(value=value))
                )

    if len(config_keywords) > 0:
        registry.register_import("pydantic.ConfigDict")
        return [
            ast.Assign(
                targets=[ast.Name(id="model_config", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="ConfigDict", ctx=ast.Load()),
                    args=[],
                    keywords=config_keywords,
                ),
            )
        ]
    else:
        return []


def add_typename_recursively(
    selection_set: SelectionSetNode | None, skip: bool = False
) -> None:
    if selection_set is None:
        return

    # Collect all existing fields in the selection set
    selections = list(selection_set.selections)
    has_typename = any(
        isinstance(field, FieldNode) and field.name.value == "__typename"
        for field in selections
    )

    # Add __typename if it's not already present
    if not has_typename and not skip:
        selections.append(
            FieldNode(
                name=NameNode(value="__typename"),
                arguments=[],
                directives=[],
                selection_set=None,
            )
        )

    # Apply the function recursively to nested selection sets
    for field in selections:
        if isinstance(field, FieldNode) and field.selection_set:
            add_typename_recursively(field.selection_set)

    # Update the selection set with potentially added __typename fields
    selection_set.selections = tuple(selections)


def auto_add_typename_field_to_all_objects(document: DocumentNode) -> DocumentNode:
    for definition in document.definitions:
        if isinstance(definition, (OperationDefinitionNode, FragmentDefinitionNode)):
            add_typename_recursively(
                definition.selection_set,
                skip=isinstance(definition, OperationDefinitionNode),
            )

    return document


def parse_documents(
    client_schema: GraphQLSchema, scan_glob: str, config: GeneratorConfig
) -> DocumentNode:
    """ """
    if not scan_glob:
        raise GenerationError("Couldnt find documents glob")

    x = glob.glob(scan_glob, recursive=True)
    x.sort()  # Ensure deterministic order

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

    errors = validate(client_schema, nodes, rules=config.get_document_rules())
    if len(errors) > 0:
        raise InvalidDocuments(
            "Invalid Documents \n" + "\n".join(str(e) for e in errors)
        )

    nodes = auto_add_typename_field_to_all_objects(nodes)

    return nodes


fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


def auto_add_typename_field_to_fragment_str(fragment_str: str) -> str:
    x = parse(fragment_str)
    for fragment in x.definitions:
        if isinstance(fragment, FragmentDefinitionNode):
            selections = list(fragment.selection_set.selections)
            if not any(
                isinstance(field, FieldNode) and field.name.value == "__typename"
                for field in selections
            ):
                selections.append(
                    FieldNode(
                        name=NameNode(value="__typename"),
                        arguments=[],
                        directives=[],
                        selection_set=None,
                    )
                )
                fragment.selection_set.selections = tuple(selections)

    return print_ast(x)


def replace_iteratively(
    pattern: str,
    registry: ClassRegistry,
    taken: list[str] = [],
) -> str:
    """Replaces the fragments in the pattern with their definitions"""
    z = set(fragment_searcher.findall(pattern))  # only set is important

    new_fragments = [new_f for new_f in z if new_f not in taken and new_f != ""]
    new_fragments.sort()

    if not new_fragments:
        return pattern
    else:
        try:
            level_down_pattern = "\n\n".join(
                [
                    auto_add_typename_field_to_fragment_str(
                        registry.get_fragment_document(key)
                    )
                    for key in new_fragments
                ]
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
    typename: str, config: GeneratorConfig, registry: ClassRegistry
) -> List[ast.Name]:
    if typename in config.additional_bases:
        for base in config.additional_bases[typename]:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in config.additional_bases[typename]
        ]
    return []


def is_oneof_input_type(graphql_type) -> bool:
    """Whether an input object type is declared with the spec ``@oneOf`` directive.

    graphql-core 3.3+ exposes this as ``is_one_of``; on 3.2 the directive is only
    visible on the SDL ``ast_node`` (which is ``None`` for introspected schemas,
    where ``@oneOf`` is therefore undetectable)."""
    if getattr(graphql_type, "is_one_of", False):
        return True
    ast_node = getattr(graphql_type, "ast_node", None)
    if ast_node is None:
        return False
    return any(directive.name.value == "oneOf" for directive in ast_node.directives)


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
    type: TypeNode,
    registry: ClassRegistry,
    optional: bool = True,
    overwrite_final: Optional[Union[str, ast.expr]] = None,
) -> ast.expr:
    if isinstance(type, NonNullTypeNode):
        return recurse_type_annotation(
            type.type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, ListTypeNode):
        if optional:
            registry.register_import("typing.List")
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name(id="List", ctx=ast.Load()),
                    slice=recurse_type_annotation(
                        type.type, registry, overwrite_final=overwrite_final
                    ),
                ),
            )

        registry.register_import("typing.List")
        return ast.Subscript(
            value=ast.Name(id="List", ctx=ast.Load()),
            slice=recurse_type_annotation(
                type.type, registry, overwrite_final=overwrite_final
            ),
        )

    if isinstance(type, NamedTypeNode):
        x = None
        if overwrite_final is not None:
            x = (
                overwrite_final
                if isinstance(overwrite_final, ast.expr)
                else ast.Name(id=overwrite_final, ctx=ast.Load())
            )
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
                        raise NotImplementedError(
                            f"Could not find corresponding type for type '{type.name.value}'. Did you register this scalar?"
                        )

        if not x:
            raise Exception(f"Could not set value for {type}")

        if optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=x,
            )

        return x

    raise NotImplementedError("oisnosin")


def recurse_outputtype_annotation(
    type: GraphQLNamedOutputType,
    registry: ClassRegistry,
    optional: bool = True,
    overwrite_final: Optional[str] = None,
) -> ast.expr:
    if isinstance(type, GraphQLNonNull):
        # If the type is non-null, we need to recurse into the inner type
        type = type.of_type

        return recurse_outputtype_annotation(
            type.of_type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, GraphQLList):
        if optional:
            registry.register_import("typing.List")
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name(id="List", ctx=ast.Load()),
                    slice=recurse_outputtype_annotation(
                        type.of_type, registry, overwrite_final=overwrite_final
                    ),
                ),
            )

        registry.register_import("typing.List")
        return ast.Subscript(
            value=ast.Name(id="List", ctx=ast.Load()),
            slice=recurse_outputtype_annotation(
                type.of_type, registry, overwrite_final=overwrite_final
            ),
        )

    if isinstance(type, GraphQLEnumType):
        if optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=registry.reference_enum(type.name, "", allow_forward=False),
            )

        return registry.reference_enum(type.name, "", allow_forward=False)

    if isinstance(type, GraphQLScalarType):
        if optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(type.name),
            )

        else:
            return registry.reference_scalar(type.name)

    if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType)):
        assert overwrite_final, "Needs to be set"
        if optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Name(id=overwrite_final, ctx=ast.Load()),
            )

        else:
            return ast.Name(id=overwrite_final, ctx=ast.Load())

    raise NotImplementedError(
        f"recurse over {type.__class__.__name__}"
    )  # pragma: no cover


def recurse_outputtype_label(
    type: GraphQLOutputType,
    registry: ClassRegistry,
    optional: bool = True,
    overwrite_final: Optional[str] = None,
) -> str:
    if isinstance(type, GraphQLNonNull):  # pragma: no cover
        return recurse_outputtype_label(
            type.of_type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, GraphQLList):
        inner = list_label(
            recurse_outputtype_label(
                type.of_type, registry, overwrite_final=overwrite_final
            ),
            registry.config,
        )
        return optional_label(inner, registry.config) if optional else inner

    if isinstance(type, GraphQLEnumType):
        inner = registry.reference_enum(type.name, "", allow_forward=False).id
        return optional_label(inner, registry.config) if optional else inner

    if isinstance(type, GraphQLScalarType):
        inner = registry.reference_scalar(type.name).id
        return optional_label(inner, registry.config) if optional else inner

    if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType)):
        assert overwrite_final, "Needs to be set"
        return (
            optional_label(overwrite_final, registry.config)
            if optional
            else overwrite_final
        )

    raise NotImplementedError("oisnosin")


def recurse_type_label(
    type: TypeNode,
    registry: ClassRegistry,
    optional: bool = True,
    overwrite_final: Optional[str] = None,
) -> str:
    if isinstance(type, NonNullTypeNode):
        return recurse_type_label(
            type.type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, ListTypeNode):
        inner = list_label(
            recurse_type_label(type.type, registry, overwrite_final=overwrite_final),
            registry.config,
        )
        return optional_label(inner, registry.config) if optional else inner

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
                        raise NotImplementedError(
                            f"Could not find correspoinding type labler for {type.name.value}"
                        )

        label = x.id if isinstance(x, ast.Name) else x.value
        return optional_label(label, registry.config) if optional else label

    raise NotImplementedError("Not implemented for this type")


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


def convert_default_value_to_ast(value):
    """Converts a coerced Python default value (as stored on a GraphQL input
    field / argument) into an AST node usable as a pydantic field default."""
    if value is Undefined:
        return None
    if value is None:
        return ast.Constant(value=None)
    if isinstance(value, str):
        return ast.Constant(value=value)
    if isinstance(value, bool):
        return ast.Constant(value=value)
    if isinstance(value, int):
        return ast.Constant(value=value)
    if isinstance(value, float):
        return ast.Constant(value=value)
    if isinstance(value, list):
        return ast.List(
            elts=[convert_default_value_to_ast(x) for x in value], ctx=ast.Load()
        )
    if isinstance(value, dict):
        keys = []
        values = []
        for key, inner in value.items():
            keys.append(ast.Constant(value=key))
            values.append(convert_default_value_to_ast(inner))
        return ast.Dict(keys=keys, values=values)
    raise NotImplementedError(f"Unknown default value {repr(value)}")


def compose_field_documentation(
    description=None,
    deprecation_reason=None,
    default_string=None,
    include_metadata=True,
):
    """Builds a field's human-readable documentation. When ``include_metadata`` is
    True the GraphQL deprecation reason and default value are folded into the text
    alongside the description; otherwise only the plain description is returned.
    Returns ``None`` when there is nothing to document."""
    if not include_metadata:
        return description or None

    parts = []
    if description:
        parts.append(description)
    if deprecation_reason:
        parts.append(f"DEPRECATED: {deprecation_reason}")
    if default_string is not None:
        parts.append(f"Default: {default_string}")
    return "\n".join(parts) if parts else None


def annotate_field_metadata(
    annotation,
    registry,
    default_value_ast=None,
    deprecation_reason=None,
):
    """Wraps a field annotation in ``Annotated[T, GraphQLDefault(...), Deprecated(...)]``
    when the field carries a GraphQL schema default and/or a deprecation reason.

    ``default_value_ast`` is a prebuilt ``ast.expr`` (pass ``None`` for no default
    marker; an explicit-null default passes ``ast.Constant(value=None)``). The
    marker classes are resolved through the registry, which either imports a
    user-provided override or emits a generated builtin."""
    markers = []
    if default_value_ast is not None:
        markers.append(
            ast.Call(
                func=registry.reference_graphql_default(),
                args=[default_value_ast],
                keywords=[],
            )
        )
    if deprecation_reason is not None:
        markers.append(
            ast.Call(
                func=registry.reference_deprecated(),
                args=[ast.Constant(value=deprecation_reason)],
                keywords=[],
            )
        )

    if not markers:
        return annotation

    registry.register_import("typing.Annotated")
    return ast.Subscript(
        value=ast.Name(id="Annotated", ctx=ast.Load()),
        slice=ast.Tuple(elts=[annotation, *markers], ctx=ast.Load()),
        ctx=ast.Load(),
    )
