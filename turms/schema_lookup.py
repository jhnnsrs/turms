"""Schema lookups turms needs, on what graphql-core 3.2 and 3.3 both export.

graphql-core 3.3 removed ``graphql.utilities.type_info.get_field_def`` and
``graphql.utilities.get_operation_root_type``, and moved argument and input-field
defaults from ``default_value`` to ``default`` (a ``GraphQLDefaultInput``). These are
turms's own versions, so the rest of turms works against either.
"""

from typing import Any, Optional, cast

from graphql import (
    GraphQLArgument,
    GraphQLInputField,
    coerce_input_value,
    value_from_ast,
    FieldNode,
    GraphQLError,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLType,
    OperationDefinitionNode,
    SchemaMetaFieldDef,
    TypeMetaFieldDef,
    TypeNameMetaFieldDef,
    is_composite_type,
    is_interface_type,
    is_object_type,
)


try:
    from graphql import coerce_input_literal as _coerce_literal
except ImportError:  # graphql-core 3.2, where value_from_ast fills nested defaults
    _coerce_literal = value_from_ast


def get_field_def(
    schema: GraphQLSchema, parent_type: GraphQLType, field_node: FieldNode
) -> Optional[GraphQLField]:
    """The definition of the field ``field_node`` selects on ``parent_type``.

    Resolves the introspection meta fields as well. ``None`` when the parent type
    has no such field, or is a union (which has no fields of its own).
    """
    name = field_node.name.value
    if name == "__schema" and schema.query_type is parent_type:
        return SchemaMetaFieldDef
    if name == "__type" and schema.query_type is parent_type:
        return TypeMetaFieldDef
    if name == "__typename" and is_composite_type(parent_type):
        return TypeNameMetaFieldDef
    if is_object_type(parent_type) or is_interface_type(parent_type):
        fields_of = cast(GraphQLObjectType | GraphQLInterfaceType, parent_type)
        return fields_of.fields.get(name)
    return None


def get_operation_root_type(
    schema: GraphQLSchema, operation: OperationDefinitionNode
) -> GraphQLObjectType:
    """The root type (query, mutation or subscription) an operation selects on.

    Raises:
        GraphQLError: If the schema does not define that root type.
    """
    root_type = schema.get_root_type(operation.operation)
    if root_type is None:
        raise GraphQLError(
            f"Schema is not configured to execute {operation.operation.value} operation.",
            operation,
        )
    return root_type


def get_default_value(input_value: GraphQLArgument | GraphQLInputField) -> Any:  # noqa: ANN401
    """The coerced default of an argument or input field, or ``Undefined`` if it has none.

    ``None`` is a real default (``= null``), distinct from having none. graphql-core
    3.2 stores it coerced in ``default_value``; 3.3 leaves that ``Undefined`` and keeps
    the default in ``default``, as a literal (from SDL or introspection) or a value.
    """
    default = getattr(input_value, "default", None)
    if default is None:
        return input_value.default_value
    if default.literal is not None:
        # 3.3's value_from_ast reads the deprecated `default_value` and so skips a
        # nested input field's own default; coerce_input_literal (3.3 only) does not.
        return _coerce_literal(default.literal, input_value.type)
    return coerce_input_value(default.value, input_value.type)
