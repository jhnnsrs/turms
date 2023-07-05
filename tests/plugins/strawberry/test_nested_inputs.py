from turms.config import GeneratorConfig
from turms.plugins.strawberry import StrawberryPlugin
from turms.run import build_ast_schema, generate_ast, parse_asts_to_string
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
    #tracks: [RemoveItemFromPlaylistTrackInput!]!
}
"""


def _generate_schema(schema: str):
    config = GeneratorConfig(scalar_definitions={"_Any": "typing.Any"})

    generated_ast = generate_ast(
        config,
        schema=build_ast_schema(parse(schema)),
        plugins=[StrawberryPlugin()],
        skip_forwards=True,
    )

    return parse_asts_to_string(generated_ast)


def test_generates_schema(snapshot):
    snapshot.snapshot_dir = SNAPSHOTS_DIR
    snapshot.assert_match(_generate_schema(schema), "nested_inputs.py")
