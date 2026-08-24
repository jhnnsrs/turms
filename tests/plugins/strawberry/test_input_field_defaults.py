"""An input field a caller may omit - because it is nullable, or because it
carries a schema default - must get a Python default in the generated
dataclass. Without one, strawberry has no value to fall back on when a
client omits the field, and construction fails with a
"missing required keyword-only argument" TypeError even though the GraphQL
schema says the field is optional to provide.
"""

import pathlib

from graphql import parse

from turms.config import GeneratorConfig
from turms.plugins.strawberry import StrawberryPlugin
from turms.processors.isort import IsortProcessor
from turms.run import build_ast_schema, generate_ast, generate_code

from ...utils import unit_test_with

SNAPSHOTS_DIR = pathlib.Path(__file__).parent / "snapshots"

schema = """
type Query {
    hi: String
}

input FieldDefaultsInput {
    nullableNoDefault: String
    nullableWithDefault: String = "fallback"
    requiredWithDefault: String! = "required-fallback"
    requiredNoDefault: String!
}
"""

list_default_schema = """
type Query {
    hi: String
}

input ListDefaultInput {
    tags: [String!] = ["a", "b"]
}
"""


def _config():
    return GeneratorConfig(scalar_definitions={"_Any": "typing.Any"}, skip_forwards=True)


def _generate_schema(schema: str):
    return generate_code(
        _config(),
        schema=build_ast_schema(parse(schema)),
        plugins=[StrawberryPlugin()],
        processors=[IsortProcessor()],
    )


def test_generates_schema(snapshot):
    snapshot.snapshot_dir = SNAPSHOTS_DIR
    snapshot.assert_match(_generate_schema(schema), "input_field_defaults.py")


def test_omitting_every_optional_field_constructs_successfully():
    """The exact crash this fix addresses: a caller supplying only the
    required field must not hit a missing-keyword-argument TypeError for
    fields it left out."""
    generated_ast = generate_ast(
        _config(),
        build_ast_schema(parse(schema)),
        plugins=[StrawberryPlugin()],
    )

    unit_test_with(
        generated_ast,
        "i = FieldDefaultsInput(requiredNoDefault='x')\n"
        "assert i.nullableNoDefault is None\n"
        "assert i.nullableWithDefault == 'fallback'\n"
        "assert i.requiredWithDefault == 'required-fallback'\n"
        "assert i.requiredNoDefault == 'x'\n",
    )


def test_omitted_list_default_uses_a_fresh_list_each_time():
    """A mutable default must go through default_factory, not default= -
    otherwise every instance would share (and could mutate) the same list."""
    generated_ast = generate_ast(
        _config(),
        build_ast_schema(parse(list_default_schema)),
        plugins=[StrawberryPlugin()],
    )

    unit_test_with(
        generated_ast,
        "a = ListDefaultInput()\n"
        "b = ListDefaultInput()\n"
        "assert a.tags == ['a', 'b']\n"
        "a.tags.append('c')\n"
        "assert b.tags == ['a', 'b']\n",
    )
