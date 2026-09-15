"""Regressions for schema fidelity in the Strawberry plugin.

Each case corresponds to output that made the served schema differ from the SDL
the client generated its types from. ``unit_test_with`` executes the generated
module with ``test_string`` appended, so the assertions below run against a
schema actually built from generated code.
"""

from graphql import parse

from turms.config import GeneratorConfig
from turms.plugins.strawberry import StrawberryPlugin, StrawberryPluginConfig
from turms.run import build_ast_schema, generate_ast

from ...utils import parse_to_code, unit_test_with


def _generate(schema: str, plugin: StrawberryPlugin = None):
    return generate_ast(
        GeneratorConfig(scalar_definitions={"_Any": "typing.Any"}, skip_forwards=True),
        build_ast_schema(parse(schema)),
        plugins=[plugin or StrawberryPlugin()],
        skip_forwards=True,
    )


union_schema = """
type Invoice {
    n: Int!
}

type Receipt {
    n: Int!
}

union ClientDocument = Invoice | Receipt

type Query {
    docs: [ClientDocument!]!
    one: ClientDocument
}
"""


def test_union_keeps_its_schema_name():
    """strawberry names an unnamed union after its members, so a union would be
    served as ``InvoiceReceipt`` and no longer match the SDL."""
    generated_ast = _generate(union_schema)

    unit_test_with(
        generated_ast,
        """
import strawberry
from strawberry.printer import print_schema

sdl = print_schema(strawberry.Schema(query=Query))

assert "union ClientDocument = Invoice | Receipt" in sdl, sdl
assert "InvoiceReceipt" not in sdl, sdl
assert "docs: [ClientDocument!]!" in sdl, sdl
assert "one: ClientDocument" in sdl, sdl
""",
    )


id_schema = """
type Item {
    id: ID!
}

type Query {
    item(id: ID!): Item
}
"""


def test_id_scalar_stays_an_id():
    """The shared scalar map resolves ``ID`` to ``str`` for the pydantic
    plugins, which turned every ``ID`` in a Strawberry schema into ``String``."""
    generated_ast = _generate(id_schema)

    unit_test_with(
        generated_ast,
        """
import strawberry
from strawberry.printer import print_schema

sdl = print_schema(strawberry.Schema(query=Query))

assert "item(id: ID!): Item" in sdl, sdl
assert "id: ID!" in sdl, sdl
assert ": String" not in sdl, sdl
""",
    )


def test_explicit_scalar_definition_wins_over_the_plugin_default():
    """A user who maps ``ID`` themselves means it."""
    generated_ast = generate_ast(
        GeneratorConfig(scalar_definitions={"ID": "str"}, skip_forwards=True),
        build_ast_schema(parse(id_schema)),
        plugins=[StrawberryPlugin()],
        skip_forwards=True,
    )

    unit_test_with(
        generated_ast,
        """
import strawberry
from strawberry.printer import print_schema

sdl = print_schema(strawberry.Schema(query=Query))

assert "item(id: String!): Item" in sdl, sdl
""",
    )


input_directive_schema = """
directive @secured(requires: String!) on INPUT_FIELD_DEFINITION

input UserInput {
    roles: [String!]! @secured(requires: "hasRole")
    plain: String
}

type Query {
    q(i: UserInput!): String
}
"""


def test_input_field_directives_are_kept():
    """Dropping a directive from an input field removes the authorization check
    from the served schema, which fails open."""
    generated_ast = _generate(input_directive_schema)

    unit_test_with(
        generated_ast,
        """
import strawberry
from strawberry.printer import print_schema

sdl = print_schema(strawberry.Schema(query=Query))

assert "roles: [String!]! @secured(requires:" in sdl, sdl
assert "plain: String" in sdl, sdl
""",
    )


custom_scalar_schema = """
scalar Slug

type Query {
    slug: Slug
}
"""


def test_generate_scalars_flag_is_honoured():
    """Scalar generation was gated on ``generate_directives``, so turning it off
    did nothing."""
    config = GeneratorConfig(scalar_definitions={"Slug": "str"}, skip_forwards=True)
    plugin = StrawberryPlugin(config=StrawberryPluginConfig(generate_scalars=False))

    code = parse_to_code(
        generate_ast(
            config,
            build_ast_schema(parse(custom_scalar_schema)),
            plugins=[plugin],
            skip_forwards=True,
        )
    )

    assert "strawberry.scalar" not in code, code
