import ast
import glob
import re
from typing import List, Optional, Set, Union

from graphql import (
    BooleanValueNode,
    FloatValueNode,
    FragmentDefinitionNode,
    GraphQLEnumType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
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
    SelectionSetNode,
    StringValueNode,
    ValueNode,
    parse,
    print_ast,
    validate,
)
from graphql.error.graphql_error import GraphQLError
from graphql.language.ast import DocumentNode, FieldNode, NameNode
from graphql.utilities.build_client_schema import GraphQLSchema

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


class FragmentNotFoundError(GenerationError):
    pass


class NoDocumentsFoundError(GenerationError):
    pass


class InvalidDocuments(GenerationError):
    pass


class NoScalarEquivalentDefined(GenerationError):
    pass


def target_from_node(node: FieldNode) -> str:
    """Extacts the field name from a FieldNode. If alias is present, it will be used instead of the name"""
    return (
        node.alias.value if hasattr(node, "alias") and node.alias else node.name.value
    )


def non_typename_fields(node: FieldNode) -> List[FieldNode]:
    """Returns all fields in a FieldNode that are not __typename"""
    if not node.selection_set:
        return []
    return [field for field in node.selection_set.selections if not (isinstance(field, FieldNode) and field.name.value == "__typename")]


def inspect_operation_for_documentation(operation: OperationDefinitionNode):
    """Checks for operation level documentatoin"""

    definition = operation.loc.source.body.splitlines()[
        operation.loc.source.get_location(operation.loc.start).line
        - 1 : operation.loc.source.get_location(
            operation.selection_set.selections[0].loc.start
        ).line
        - 1
    ]
    doc = []
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

def generate_generic_typename_field(
    registry: ClassRegistry, config: GeneratorConfig
):
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


def generate_config_dict(
    graphQLType: GraphQLTypes,
    config: GeneratorConfig,
    registy: ClassRegistry,
    typename: str = None,
):
    """Generates the config class for a specific type version 2

    It will append the config class to the registry, and set the frozen
    attribute for the class to True, if the freeze config is enabled and
    the type appears in the freeze list.

    It will also add config attributes to the class, if the type appears in
    'additional_config' in the config file.

    """

    config_keywords = []

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
                if config.options.allow_mutation is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="allow_mutation",
                            value=ast.Constant(value=config.options.allow_mutation),
                        )
                    )

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

                if config.options.orm_mode is not None:
                    config_keywords.append(
                        ast.keyword(
                            arg="orm_mode",
                            value=ast.Constant(value=config.options.orm_mode),
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
        registy.register_import("pydantic.ConfigDict")
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


def generate_config_class_pydantic(
    graphQLType: GraphQLTypes, config: GeneratorConfig, typename: str = None
):
    """Generates the config class for a specific type

    It will append the config class to the registry, and set the frozen
    attribute for the class to True, if the freeze config is enabled and
    the type appears in the freeze list.

    It will also add config attributes to the class, if the type appears in
    'additional_config' in the config file.

    """

    config_fields = []

    if config.freeze.enabled:
        if graphQLType in config.freeze.types:
            if config.freeze.exclude and typename in config.freeze.exclude:
                pass
            elif config.freeze.include and typename not in config.freeze.include:
                pass
            else:
                config_fields.append(
                    ast.Assign(
                        targets=[ast.Name(id="frozen", ctx=ast.Store())],
                        value=ast.Constant(value=True),
                    )
                )

    if config.options.enabled:
        if graphQLType in config.options.types:
            if config.options.exclude and typename in config.options.exclude:
                pass
            elif config.options.include and typename not in config.options.include:
                pass
            else:
                if config.options.allow_mutation is not None:
                    config_fields.append(
                        ast.Assign(
                            targets=[ast.Name(id="allow_mutation", ctx=ast.Store())],
                            value=ast.Constant(value=config.options.allow_mutation),
                        )
                    )

                if config.options.extra is not None:
                    config_fields.append(
                        ast.Assign(
                            targets=[ast.Name(id="extra", ctx=ast.Store())],
                            value=ast.Constant(value=config.options.extra),
                        )
                    )

                if config.options.validate_assignment is not None:
                    config_fields.append(
                        ast.Assign(
                            targets=[
                                ast.Name(id="validate_assignment", ctx=ast.Store())
                            ],
                            value=ast.Constant(
                                value=config.options.validate_assignment
                            ),
                        )
                    )

                if config.options.allow_population_by_field_name is not None:
                    config_fields.append(
                        ast.Assign(
                            targets=[
                                ast.Name(
                                    id="allow_population_by_field_name", ctx=ast.Store()
                                )
                            ],
                            value=ast.Constant(
                                value=config.options.allow_population_by_field_name
                            ),
                        )
                    )

                if config.options.orm_mode is not None:
                    config_fields.append(
                        ast.Assign(
                            targets=[ast.Name(id="orm_mode", ctx=ast.Store())],
                            value=ast.Constant(value=config.options.orm_mode),
                        )
                    )

                if config.options.use_enum_values is not None:
                    config_fields.append(
                        ast.Assign(
                            targets=[ast.Name(id="use_enum_values", ctx=ast.Store())],
                            value=ast.Constant(value=config.options.use_enum_values),
                        )
                    )

    if typename:
        if typename in config.additional_config:
            for key, value in config.additional_config[typename].items():
                config_fields.append(
                    ast.Assign(
                        targets=[ast.Name(id=key, ctx=ast.Store())],
                        value=ast.Constant(value=value),
                    )
                )

    if len(config_fields) > 0:
        config_fields.insert(
            0,
            ast.Expr(
                value=ast.Constant(value="A config class"),
            ),
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


def generate_pydantic_config(
    graphQLType: GraphQLTypes,
    config: GeneratorConfig,
    registry: ClassRegistry,
    typename: str = None,
):
    if config.pydantic_version == "v2":
        return generate_config_dict(graphQLType, config, registry, typename)
    else:
        return generate_config_class_pydantic(graphQLType, config, typename)



def add_typename_recursively(selection_set: SelectionSetNode, skip=False) -> None:
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
            add_typename_recursively(definition.selection_set, skip=isinstance(definition, OperationDefinitionNode))
    
    
    return document


def parse_documents(client_schema: GraphQLSchema, scan_glob) -> DocumentNode:
    """ """
    if not scan_glob:
        raise GenerationError("Couldnt find documents glob")

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
            if not any(isinstance(field, FieldNode) and field.name.value == "__typename" for field in selections):
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
                [auto_add_typename_field_to_fragment_str(registry.get_fragment_document(key)) for key in new_fragments]
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
    type: GraphQLOutputType,
    registry: ClassRegistry,
    optional=True,
    overwrite_final: Optional[str] = None,
) -> ast.expr:
    if isinstance(type, GraphQLNonNull):
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

    raise NotImplementedError(f"recurse over {type.__class__.__name__}")  # pragma: no cover


def recurse_outputtype_label(
    type: GraphQLOutputType,
    registry: ClassRegistry,
    optional=True,
    overwrite_final: Optional[str] = None,
):
    if isinstance(type, GraphQLNonNull):  # pragma: no cover
        return recurse_outputtype_label(
            type.of_type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, GraphQLList):
        if optional:
            return (
                "Optional[List["
                + recurse_outputtype_label(
                    type.of_type, registry, overwrite_final=overwrite_final
                )
                + "]]"
            )

        return (
            "List["
            + recurse_outputtype_label(
                type.of_type, registry, overwrite_final=overwrite_final
            )
            + "]"
        )

    if isinstance(type, GraphQLEnumType):
        if optional:
            return (
                "Optional["
                + registry.reference_enum(type.name, "", allow_forward=False).id
                + "]"
            )

        return registry.reference_enum(type.name, "", allow_forward=False).id

    if isinstance(type, GraphQLScalarType):
        if optional:
            return "Optional[" + registry.reference_scalar(type.name).id + "]"

        else:
            return registry.reference_scalar(type.name).id

    if isinstance(type, (GraphQLObjectType, GraphQLInterfaceType, GraphQLUnionType)):
        assert overwrite_final, "Needs to be set"
        if optional:
            return "Optional[" + overwrite_final + "]"

        else:
            return overwrite_final

    raise NotImplementedError("oisnosin")


def recurse_type_label(
    type: NamedTypeNode,
    registry: ClassRegistry,
    optional=True,
    overwrite_final: Optional[str] = None,
):
    if isinstance(type, NonNullTypeNode):
        return recurse_type_label(
            type.type, registry, optional=False, overwrite_final=overwrite_final
        )

    if isinstance(type, ListTypeNode):
        if optional:
            return (
                "Optional[List["
                + recurse_type_label(
                    type.type, registry, overwrite_final=overwrite_final
                )
                + "]]"
            )

        return (
            "List["
            + recurse_type_label(type.type, registry, overwrite_final=overwrite_final)
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
                        raise NotImplementedError(
                            f"Could not find correspoinding type labler for {type.name.value}"
                        )

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
