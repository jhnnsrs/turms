from turms.config import GeneratorConfig
from turms.plugins.strawberry import StrawberryPlugin
from turms.processors.isort import IsortProcessor
from turms.run import build_ast_schema, generate_code, parse_asts_to_string
from graphql import parse
import pathlib


SNAPSHOTS_DIR = pathlib.Path(__file__).parent / "snapshots"

schema = """
type Query {
    hi: String
}

input RemoveItemFromPlaylistTrackInput {
    uri: String!
}

input RemoveItemFromPlaylistInput {
    playlistId: ID!
    snapshotId: ID
    tracks: [RemoveItemFromPlaylistTrackInput!]!
}
"""


def _generate_schema(schema: str):
    config = GeneratorConfig(
        scalar_definitions={"_Any": "typing.Any"}, skip_forwards=True
    )

    code = generate_code(
        config,
        schema=build_ast_schema(parse(schema)),
        plugins=[StrawberryPlugin()],
        processors=[IsortProcessor()],
    )

    return code


def test_generates_schema(snapshot):
    snapshot.snapshot_dir = SNAPSHOTS_DIR
    snapshot.assert_match(_generate_schema(schema), "nested_inputs.py")
