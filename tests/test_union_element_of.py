"""Tests for the custom ``unionElementOf`` directive (discriminated input unions).

Mirrors the mikro pattern: lean member inputs annotated with the repeatable
``@unionElementOf(union, discriminator, key)`` directive, and placeholder input
types that get replaced by an ``Annotated[Union[...], Field(discriminator=...)]``
alias. The injected ``Literal`` discriminator must survive the proxy contract's
``dict(by_alias=True, exclude_unset=True)`` dump, because the server requires it.
"""

import pytest
from graphql import parse

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import build_ast_schema, generate_ast
from turms.stylers.default import DefaultStyler

from .utils import unit_test_with

schema_sdl = """
directive @unionElementOf(union: String!, discriminator: String!, key: String!) repeatable on INPUT_OBJECT

input AffineTransformInput @unionElementOf(union: "TransformInput", discriminator: "kind", key: "AFFINE") @unionElementOf(union: "RelationInput", discriminator: "kind", key: "AFFINE") {
  affine: [[Float!]!]!
}

input ScaleTransformInput @unionElementOf(union: "TransformInput", discriminator: "kind", key: "SCALE") @unionElementOf(union: "RelationInput", discriminator: "kind", key: "SCALE") {
  scale: [Float!]!
}

input FieldTransformInput @unionElementOf(union: "TransformInput", discriminator: "kind", key: "FIELD") {
  field: ID!
}

input TransformInput {
  kind: String!
  scale: [Float!]
  affine: [[Float!]!]
  field: ID
}

input RelationInput {
  kind: String!
  scale: [Float!]
  affine: [[Float!]!]
}

input CreateTransformationInput {
  name: String
  transform: TransformInput!
  relation: RelationInput
}

type Transformation {
  id: ID!
}

type Query {
  hello: String
}

type Mutation {
  createTransformation(input: CreateTransformationInput!): Transformation
}
"""

operation = """
mutation CreateTransformation($input: CreateTransformationInput!) {
  createTransformation(input: $input) {
    id
  }
}
"""


def _generate(tmp_path, pydantic_version, sdl=schema_sdl):
    doc = tmp_path / "ops.graphql"
    doc.write_text(operation)

    config = GeneratorConfig(
        pydantic_version=pydantic_version,
        documents=str(tmp_path / "**/*.graphql"),
    )
    return generate_ast(
        config,
        build_ast_schema(parse(sdl)),
        stylers=[DefaultStyler()],
        plugins=[InputsPlugin(), ObjectsPlugin(), OperationsPlugin()],
    )


def test_members_and_discriminated_union(tmp_path):
    """Members get an injected Literal discriminator, the placeholder becomes a
    discriminated union, and repeatable directives put a member in two unions."""
    generated_ast = _generate(tmp_path, "v2")

    unit_test_with(
        generated_ast,
        """
        # The placeholder is an Annotated alias, not a class.
        assert not isinstance(TransformInput, type)
        assert not isinstance(RelationInput, type)

        # Discriminated validation from a dict picks the right member.
        parsed = CreateTransformationInput(transform={'kind': 'SCALE', 'scale': [2.0]})
        assert isinstance(parsed.transform, ScaleTransformInput), parsed.transform

        # A member of both unions is valid in both positions.
        both = CreateTransformationInput(
            transform=AffineTransformInput(affine=[[1.0]]),
            relation=AffineTransformInput(affine=[[1.0]]),
        )
        assert both.relation.kind == 'AFFINE'

        # FieldTransformInput is only a TransformInput member.
        CreateTransformationInput(transform=FieldTransformInput(field='1'))
        try:
            CreateTransformationInput(
                transform=FieldTransformInput(field='1'),
                relation=FieldTransformInput(field='1'),
            )
        except Exception:
            pass
        else:
            raise AssertionError('FieldTransformInput must not validate as RelationInput')
        """,
    )


def test_discriminator_survives_exclude_unset(tmp_path):
    """The injected discriminator is never explicitly set by the caller, but the
    server requires it: it must survive an exclude_unset dump."""
    generated_ast = _generate(tmp_path, "v2")

    unit_test_with(
        generated_ast,
        """
        wire = CreateTransformationInput(
            transform=AffineTransformInput(affine=[[1.0, 2.0]])
        ).dict(by_alias=True, exclude_unset=True)
        assert wire == {'transform': {'kind': 'AFFINE', 'affine': [[1.0, 2.0]]}}, wire

        args = CreateTransformation.Arguments(
            input=CreateTransformationInput(transform=ScaleTransformInput(scale=[2.0]))
        ).dict(by_alias=True, exclude_unset=True)
        assert args == {'input': {'transform': {'kind': 'SCALE', 'scale': [2.0]}}}, args
        """,
    )


def test_v1_generates_working_union(tmp_path):
    generated_ast = _generate(tmp_path, "v1")

    unit_test_with(
        generated_ast,
        """
        m = CreateTransformationInput(transform=AffineTransformInput(affine=[[1.0]]))
        assert m.transform.kind == 'AFFINE'
        """,
    )


def test_missing_directive_argument_is_error(tmp_path):
    # Declare the args as optional so graphql-core accepts the SDL and turms'
    # own validation is what rejects the incomplete directive.
    sdl = schema_sdl.replace(
        "directive @unionElementOf(union: String!, discriminator: String!, key: String!) repeatable on INPUT_OBJECT",
        "directive @unionElementOf(union: String, discriminator: String, key: String) repeatable on INPUT_OBJECT",
    ).replace(
        'input FieldTransformInput @unionElementOf(union: "TransformInput", discriminator: "kind", key: "FIELD") {',
        'input FieldTransformInput @unionElementOf(union: "TransformInput", discriminator: "kind") {',
    )
    with pytest.raises(GenerationError, match="needs 'union'"):
        _generate(tmp_path, "v2", sdl=sdl)


def test_discriminator_mismatch_is_error(tmp_path):
    sdl = schema_sdl.replace(
        '@unionElementOf(union: "TransformInput", discriminator: "kind", key: "FIELD")',
        '@unionElementOf(union: "TransformInput", discriminator: "type", key: "FIELD")',
    )
    with pytest.raises(GenerationError, match="Discriminator mismatch"):
        _generate(tmp_path, "v2", sdl=sdl)
