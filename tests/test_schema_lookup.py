"""turms.schema_lookup gives the same answers on graphql-core 3.2 and 3.3.

3.3 removed get_field_def and get_operation_root_type, and moved defaults from
``default_value`` to ``default``; these pin what turms reads in their place.
"""

from graphql import Undefined, build_schema, parse

from turms.schema_lookup import get_default_value, get_field_def, get_operation_root_type

SCHEMA = build_schema(
    """
    enum Kind { A B }
    input Policy { n: Int! = 8  kind: Kind = null }
    input Holder { listed: [Int] = 1  policy: Policy = {n: 2}  bare: Int  nulled: String = null }
    type Item { id: ID! }
    type Query { items(policy: Policy! = {n: 8}): [Item!]! }
    type Mutation { touch: Int }
    """
)


def test_defaults_are_coerced_and_fill_nested_field_defaults():
    holder = SCHEMA.type_map["Holder"].fields

    assert get_default_value(SCHEMA.query_type.fields["items"].args["policy"]) == {
        "n": 8,
        "kind": None,
    }
    assert get_default_value(holder["policy"]) == {"n": 2, "kind": None}
    assert get_default_value(holder["listed"]) == [1]


def test_no_default_is_undefined_and_a_null_default_is_none():
    holder = SCHEMA.type_map["Holder"].fields

    assert get_default_value(holder["bare"]) is Undefined
    assert get_default_value(holder["nulled"]) is None


def test_field_and_root_type_lookup():
    operation = parse("mutation { touch } query { items { id __typename } }").definitions
    mutation, query = operation

    assert get_operation_root_type(SCHEMA, mutation) is SCHEMA.mutation_type
    assert get_operation_root_type(SCHEMA, query) is SCHEMA.query_type

    items = query.selection_set.selections[0]
    assert str(get_field_def(SCHEMA, SCHEMA.query_type, items).type) == "[Item!]!"
    typename = items.selection_set.selections[1]
    assert str(get_field_def(SCHEMA, SCHEMA.type_map["Item"], typename).type) == "String!"
