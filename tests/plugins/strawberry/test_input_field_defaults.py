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
from turms.run import build_ast_schema, generate_code

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
    nullableListWithDefault: [String!] = ["a", "b"]
}
"""


def _generate_schema(schema: str):
    config = GeneratorConfig(
        scalar_definitions={"_Any": "typing.Any"}, skip_forwards=True
    )

    return generate_code(
        config,
        schema=build_ast_schema(parse(schema)),
        plugins=[StrawberryPlugin()],
        processors=[IsortProcessor()],
    )


def test_generates_schema(snapshot):
    snapshot.snapshot_dir = SNAPSHOTS_DIR
    snapshot.assert_match(_generate_schema(schema), "input_field_defaults.py")
