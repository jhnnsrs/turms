"""Tests for the GraphQLDefault / Deprecated Annotated metadata markers.

A field carrying a GraphQL schema default gets `Annotated[T, GraphQLDefault(value)]`
(the value lives on the marker; the field still defaults to None so the server
applies it via exclude_unset). A deprecated field gets `Annotated[T, Deprecated(reason)]`
and the old `DEPRECATED:` prefix is dropped. Both marker classes are generated into
the module by default, or imported from a user override via config.
"""

import pytest
from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import parse_to_code, unit_test_with

schema_sdl = """
input FilterInput {
    \"\"\"the limit\"\"\"
    limit: Int = 10
    required: String!
    old: String @deprecated(reason: "use limit")
}

type Country {
    code: String
    name: String @deprecated(reason: "renamed")
}

type Query {
    countries(filter: FilterInput, page: Int): [Country!]!
}
"""

operation = """
query GetCountries($filter: FilterInput, $page: Int = 1) {
  countries(filter: $filter, page: $page) { code }
}
"""


def _generate(tmp_path, pydantic_version="v2", **config_kwargs):
    doc = tmp_path / "ops.graphql"
    doc.write_text(operation)
    config = GeneratorConfig(
        pydantic_version=pydantic_version,
        documents=str(tmp_path / "**/*.graphql"),
        **config_kwargs,
    )
    return generate_ast(
        config,
        build_ast_schema(parse(schema_sdl)),
        stylers=[SnakeCaseStyler()],
        plugins=[InputsPlugin(), ObjectsPlugin(), OperationsPlugin()],
    )


def test_markers_are_generated(tmp_path):
    generated = parse_to_code(_generate(tmp_path))
    # Marker classes are emitted at module top.
    assert "class GraphQLDefault:" in generated
    assert "class Deprecated:" in generated


def test_input_default_marker(tmp_path):
    generated = parse_to_code(_generate(tmp_path))
    # The Field description stays the plain GraphQL description; the default is a
    # string on the marker and folded into the inline comment instead.
    assert (
        "limit: Annotated[Optional[int], GraphQLDefault('10')] = Field(default=None, description='the limit')"
        in generated
    )
    assert "'the limit\\nDefault: 10'" in generated


def test_input_deprecation_marker(tmp_path):
    generated = parse_to_code(_generate(tmp_path))
    # Marker carries the reason; the DEPRECATED warning is in the inline comment.
    assert (
        "old: Annotated[Optional[str], Deprecated('use limit')] = None" in generated
    )
    assert "'DEPRECATED: use limit'" in generated


def test_object_field_deprecation_marker(tmp_path):
    generated = parse_to_code(_generate(tmp_path))
    assert "name: Annotated[Optional[str], Deprecated('renamed')]" in generated


def test_operation_variable_default_marker(tmp_path):
    generated = parse_to_code(_generate(tmp_path))
    # $page: Int = 1 -> the Arguments field carries the GraphQLDefault marker.
    assert "Annotated[Optional[int], GraphQLDefault('1')]" in generated


def test_null_and_absent_defaults_have_no_marker(tmp_path):
    """A field with no default, or an explicit null default, gets no GraphQLDefault
    marker."""
    doc = tmp_path / "ops.graphql"
    doc.write_text("query Q { __typename }")
    sdl = """
    input N {
        withDefault: Int = 5
        nullDefault: Int = null
        plain: Int
    }
    type Query { hello(n: N): String }
    """
    from turms.plugins.inputs import InputsPluginConfig

    generated = parse_to_code(
        generate_ast(
            GeneratorConfig(documents=str(tmp_path / "**/*.graphql")),
            build_ast_schema(parse(sdl)),
            stylers=[SnakeCaseStyler()],
            plugins=[InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False))],
        )
    )
    assert "with_default: Annotated[Optional[int], GraphQLDefault('5')]" in generated
    # null / absent defaults: plain optional, no marker.
    assert "null_default: Optional[int] = Field(alias='nullDefault', default=None)" in generated
    assert "plain: Optional[int] = None" in generated


def test_opt_out_of_documentation(tmp_path):
    """document_field_metadata=False keeps the markers but drops the deprecation /
    default text from the human-readable documentation."""
    generated = parse_to_code(_generate(tmp_path, document_field_metadata=False))
    # Markers are unchanged.
    assert "GraphQLDefault('10')" in generated
    assert "Deprecated('use limit')" in generated
    # Documentation no longer carries the folded metadata.
    assert "DEPRECATED:" not in generated
    assert "Default: 10" not in generated


@pytest.mark.parametrize("pydantic_version", ["v1", "v2"])
def test_generated_code_executes(tmp_path, pydantic_version):
    """pydantic must accept the Annotated metadata at runtime (both versions)."""
    generated_ast = _generate(tmp_path, pydantic_version=pydantic_version)
    unit_test_with(
        generated_ast,
        """
        instance = FilterInput(required='x')
        assert instance.limit is None
        assert instance.required == 'x'
        """,
    )


def test_config_override_imports_instead_of_generating(tmp_path):
    """When the marker classes are overridden via config, they are imported, not
    generated."""
    generated = parse_to_code(
        _generate(
            tmp_path,
            graphql_default_class="mocks.CustomDefault",
            deprecated_class="mocks.CustomDeprecated",
        )
    )
    assert "from mocks import" in generated
    assert "CustomDefault" in generated
    assert "CustomDeprecated" in generated
    # The builtins are not generated when overridden.
    assert "class GraphQLDefault:" not in generated
    assert "class Deprecated:" not in generated


def test_config_override_executes(tmp_path):
    """The overridden markers resolve and the module runs (mocks defines them)."""
    generated_ast = _generate(
        tmp_path,
        graphql_default_class="mocks.CustomDefault",
        deprecated_class="mocks.CustomDeprecated",
    )
    unit_test_with(generated_ast, "FilterInput(required='x')")
