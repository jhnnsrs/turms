import pytest
from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import ExecuteError, parse_to_code, unit_test_with

# A schema exercising every combination of nullability and default value.
# Defaults are intentionally NOT baked into the client model: a field carrying a
# schema default becomes optional (``= None``) and is omitted on serialization so
# the GraphQL server applies its own default. See test_exclude_unset.py.
inputs = """
input DefaultInput {
    requiredWithDefault: Int! = 5
    optionalWithDefault: Int = 10
    stringWithDefault: String = "hi"
    listWithDefault: [Int!] = [1, 2, 3]
    plainOptional: String
    plainRequired: String!
}

type Query {
    hello: String
}
"""


def _generate():
    config = GeneratorConfig()
    schema = build_ast_schema(parse(inputs))
    return generate_ast(
        config,
        schema,
        stylers=[SnakeCaseStyler()],
        plugins=[
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )


def test_defaulted_fields_are_optional_none():
    """A field with a schema default is optional and defaults to None client-side
    (the value is owned by the server, not baked into the model)."""
    generated_ast = _generate()
    generated = parse_to_code(generated_ast)

    # NonNull-with-default is no longer required: optional, defaults to None, the
    # schema default is preserved (as a string) on a GraphQLDefault marker. The
    # Field carries no folded description (the schema field has none); the default
    # is documented in the inline comment instead.
    assert (
        "required_with_default: Annotated[Optional[int], GraphQLDefault('5')] = Field(alias='requiredWithDefault', default=None)"
        in generated
    )
    assert "'Default: 5'" in generated
    # nullable-with-default also defaults to None, with the value on the marker.
    assert (
        "optional_with_default: Annotated[Optional[int], GraphQLDefault('10')] = Field(alias='optionalWithDefault', default=None)"
        in generated
    )
    assert (
        "string_with_default: Annotated[Optional[str], GraphQLDefault('hi')] = Field(alias='stringWithDefault', default=None)"
        in generated
    )
    # list-with-default likewise defaults to None — the value lives on the marker.
    assert (
        "list_with_default: Annotated[Optional[List[int]], GraphQLDefault('[1, 2, 3]')] = Field(alias='listWithDefault', default=None)"
        in generated
    )
    assert "'Default: [1, 2, 3]'" in generated
    # plain optional still defaults to None and has no marker.
    assert "plain_optional: Optional[str] = Field(alias='plainOptional', default=None)" in generated
    # plain required carries no default.
    assert "Field(alias='plainRequired', default" not in generated


def test_no_default_values_are_baked():
    """The schema's literal defaults must never appear as baked pydantic defaults
    (default=/default_factory=); they live only on the GraphQLDefault marker."""
    generated = parse_to_code(_generate())

    assert "default=5" not in generated
    assert "default=10" not in generated
    assert "default='hi'" not in generated
    assert "default_factory" not in generated
    # The values appear only as strings inside GraphQLDefault(...) markers.
    assert "GraphQLDefault('5')" in generated
    assert "GraphQLDefault('[1, 2, 3]')" in generated


def test_default_values_apply_at_runtime():
    """A field with a schema default is no longer required by pydantic, and is None
    until the caller (or, on the wire, the server) provides a value."""
    generated_ast = _generate()

    unit_test_with(
        generated_ast,
        """
        instance = DefaultInput(plainRequired='x')
        assert instance.required_with_default is None
        assert instance.optional_with_default is None
        assert instance.string_with_default is None
        assert instance.list_with_default is None
        assert instance.plain_optional is None
        """,
    )


def test_required_field_without_default_still_required():
    """Regression: a required field without a default must still be required."""
    generated_ast = _generate()

    with pytest.raises(ExecuteError):
        unit_test_with(generated_ast, "DefaultInput()")
