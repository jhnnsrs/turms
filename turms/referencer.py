from typing import Dict, Set

from graphql import (
    FragmentDefinitionNode,
    GraphQLEnumType,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
    OperationDefinitionNode,
)
from graphql.language.ast import (
    DocumentNode,
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
)
from graphql.type.definition import (
    GraphQLType,
    GraphQLUnionType,
)
from graphql.utilities.build_client_schema import GraphQLSchema


class ReferenceRegistry:
    def __init__(self):
        self.objects: Set[str] = set()
        self.fragments: Set[str] = set()
        self.enums: Set[str] = set()
        self.inputs: Set[str] = set()
        self.scalars: Set[str] = set()
        self.operations: Set[str] = set()

    def register_type(self, type_name: str):
        self.objects.add(type_name)

    def register_fragment(self, type_name: str):
        self.fragments.add(type_name)

    def register_enum(self, type_name: str):
        self.enums.add(type_name)

    def register_input(self, type_name: str):
        self.inputs.add(type_name)

    def register_scalar(self, type_name: str):
        self.scalars.add(type_name)

    def is_input_registered(self, type_name: str):
        return type_name in self.inputs


def recurse_find_references(
    node: FieldNode,
    graphql_type: GraphQLType,
    client_schema: GraphQLSchema,
    registry: ReferenceRegistry,
    is_optional=True,
):
    if isinstance(
        graphql_type, (GraphQLUnionType, GraphQLObjectType, GraphQLInterfaceType)
    ):
        for sub_node in node.selection_set.selections:
            if isinstance(sub_node, FragmentSpreadNode):
                registry.register_fragment(sub_node.name.value)

            elif isinstance(sub_node, InlineFragmentNode):
                for sub_sub_node in sub_node.selection_set.selections:
                    if isinstance(sub_sub_node, FieldNode):
                        sub_sub_node_type = client_schema.get_type(
                            sub_node.type_condition.name.value
                        )

                        if sub_sub_node.name.value == "__typename":
                            continue

                        field_type = sub_sub_node_type.fields[sub_sub_node.name.value]
                        recurse_find_references(
                            sub_sub_node,
                            field_type.type,
                            client_schema,
                            registry,
                        )
            elif isinstance(sub_node, FieldNode):
                if sub_node.name.value == "__typename":
                    continue
                this_type = graphql_type.fields[sub_node.name.value]

                recurse_find_references(
                    sub_node,
                    this_type.type,
                    client_schema,
                    registry,
                )
            else:
                raise Exception("Unexpected Type")

    elif isinstance(graphql_type, GraphQLScalarType):
        registry.register_scalar(graphql_type.name)

    elif isinstance(graphql_type, GraphQLEnumType):
        registry.register_enum(graphql_type.name)

    elif isinstance(graphql_type, GraphQLNonNull):
        recurse_find_references(
            node,
            graphql_type.of_type,
            client_schema,
            registry,
            is_optional=False,
        )

    elif isinstance(graphql_type, GraphQLList):
        recurse_find_references(
            node,
            graphql_type.of_type,
            client_schema,
            registry,
            is_optional=False,
        )
    else:
        raise Exception("Unknown Type", type(graphql_type), graphql_type)


def break_recursion_loop(*args, **kwargs):
    return recurse_type_annotation(*args, **kwargs)


def recurse_type_annotation(
    field: GraphQLInputField,
    graphql_type: NamedTypeNode,
    schema: GraphQLSchema,
    registry: ReferenceRegistry,
    optional=True,
):

    if isinstance(graphql_type, NonNullTypeNode):
        return recurse_type_annotation(
            field, graphql_type.type, schema, registry, optional=False
        )

    elif isinstance(graphql_type, ListTypeNode):
        return recurse_type_annotation(field, graphql_type.type, schema, registry)

    elif isinstance(graphql_type, NamedTypeNode):
        type = schema.get_type(graphql_type.name.value)
        assert type, graphql_type
        return recurse_type_annotation(field, type, schema, registry, optional=False)

    elif isinstance(graphql_type, GraphQLNonNull):
        return recurse_type_annotation(
            field, graphql_type.of_type, schema, registry, optional=False
        )

    elif isinstance(graphql_type, GraphQLList):
        return recurse_type_annotation(
            field, graphql_type.of_type, schema, registry, optional=False
        )

    elif isinstance(graphql_type, GraphQLScalarType):
        registry.register_scalar(graphql_type.name)

    elif isinstance(graphql_type, GraphQLEnumType):
        registry.register_enum(graphql_type.name)

    elif isinstance(graphql_type, GraphQLInputObjectType):
        # Only and only is we have not registered this input object type yet
        # we need to register it (otherwise we might get into a recursion loop)
        if not registry.is_input_registered(graphql_type.name):

            registry.register_input(graphql_type.name)

            # We need to get all input objects that this graphql input object type references

            for key, node in graphql_type.fields.items():
                recurse_type_annotation(node, node.type, schema, registry)

    else:
        raise Exception("Unknown Type", field, graphql_type)


def create_reference_registry_from_documents(
    schema: GraphQLSchema, document: DocumentNode
) -> ReferenceRegistry:
    """Finds all references of types of types that are used in the documents"""

    fragments: Dict[str, FragmentDefinitionNode] = {}
    operations: Dict[str, OperationDefinitionNode] = {}

    registry = ReferenceRegistry()

    for definition in document.definitions:
        if isinstance(definition, FragmentDefinitionNode):
            fragments[definition.name.value] = definition
        if isinstance(definition, OperationDefinitionNode):
            operations[definition.name.value] = definition

    for fragment in fragments.values():
        type = schema.get_type(fragment.type_condition.name.value)
        for selection in fragment.selection_set.selections:
            if isinstance(selection, FieldNode):
                # definition
                if selection.name.value == "__typename":
                    continue
                this_type = type.fields[selection.name.value]

                recurse_find_references(
                    selection,
                    this_type.type,
                    schema,
                    registry,
                )
            elif isinstance(selection, InlineFragmentNode):
                sub_type = schema.get_type(selection.type_condition.name.value)
                for sub_selection in selection.selection_set.selections:
                    if isinstance(sub_selection, FieldNode):
                        if sub_selection.name.value == "__typename":
                            continue
                        sub_this_type = sub_type.fields[sub_selection.name.value]
                        recurse_find_references(
                            sub_selection,
                            sub_this_type.type,
                            schema,
                            registry,
                        )

    for operation in operations.values():
        type = schema.get_root_type(operation.operation)

        for argument in operation.variable_definitions:
            recurse_type_annotation(argument, argument.type, schema, registry)

        for selection in operation.selection_set.selections:
            if isinstance(selection, FieldNode):
                # definition
                if selection.name.value == "__typename":
                    continue
                this_type = type.fields[selection.name.value]

                recurse_find_references(
                    selection,
                    this_type.type,
                    schema,
                    registry,
                )

    return registry
