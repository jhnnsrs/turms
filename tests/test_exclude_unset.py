"""End-to-end tests for the "backend owns defaults" model.

Defaulted input fields / operation variables are emitted as optional ``= None``
and the generated client serializes with ``exclude_unset=True`` so that arguments
the caller never set are omitted (the server applies its own default), while an
explicitly-passed ``None`` is still transmitted.
"""

import pytest
from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from .utils import parse_to_code, unit_test_with

schema_sdl = """
input Filter {
    eq: String
    ne: String
}

type Country {
    code: String
}

type Query {
    countries(filter: Filter, limit: Int, req: Int): [Country!]!
}
"""

operation = """
query GetCountries($filter: Filter, $limit: Int = 10, $req: Int! = 5) {
  countries(filter: $filter, limit: $limit, req: $req) {
    code
  }
}
"""


def _generate(tmp_path, pydantic_version, with_funcs=False, **config_kwargs):
    doc = tmp_path / "ops.graphql"
    doc.write_text(operation)

    config = GeneratorConfig(
        pydantic_version=pydantic_version,
        documents=str(tmp_path / "**/*.graphql"),
        **config_kwargs,
    )
    plugins = [InputsPlugin(), ObjectsPlugin(), OperationsPlugin()]
    if with_funcs:
        plugins.append(
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
                        FunctionDefinition(
                            type="query", use="mocks.query", is_async=False
                        )
                    ]
                )
            )
        )
    return generate_ast(
        config,
        build_ast_schema(parse(schema_sdl)),
        stylers=[DefaultStyler()],
        plugins=plugins,
    )


@pytest.mark.parametrize("pydantic_version", ["v1", "v2"])
def test_input_omits_unset_keeps_explicit_null(tmp_path, pydantic_version):
    """An omitted input field is absent from the exclude_unset dump; an explicitly
    passed None is present as null."""
    generated_ast = _generate(tmp_path, pydantic_version)

    unit_test_with(
        generated_ast,
        """
        omitted = Filter(eq='x').dict(by_alias=True, exclude_unset=True)
        assert omitted == {'eq': 'x'}, omitted

        explicit = Filter(eq='x', ne=None).dict(by_alias=True, exclude_unset=True)
        assert explicit == {'eq': 'x', 'ne': None}, explicit
        """,
    )


@pytest.mark.parametrize("pydantic_version", ["v1", "v2"])
def test_arguments_defaulted_var_is_optional_and_omitted(tmp_path, pydantic_version):
    """A NonNull-with-default operation variable ($req: Int! = 5) is optional on the
    client and omitted when unset, so the server applies its default."""
    generated_ast = _generate(tmp_path, pydantic_version)

    unit_test_with(
        generated_ast,
        """
        empty = GetCountries.Arguments().dict(by_alias=True, exclude_unset=True)
        assert empty == {}, empty

        explicit = GetCountries.Arguments(limit=None).dict(by_alias=True, exclude_unset=True)
        assert explicit == {'limit': None}, explicit

        provided = GetCountries.Arguments(req=7).dict(by_alias=True, exclude_unset=True)
        assert provided == {'req': 7}, provided
        """,
    )


def test_unset_sentinel_override(tmp_path):
    """The UNSET sentinel type and instance can be overridden via config: they are
    imported instead of generated, and used in the function signatures."""
    generated = parse_to_code(
        _generate(
            tmp_path,
            "v2",
            with_funcs=True,
            unset_type_class="mocks.CustomUnset",
            unset_instance="mocks.CUSTOM_UNSET",
        )
    )
    # Imported, not generated.
    assert "class UnsetType:" not in generated
    assert "UNSET = UnsetType()" not in generated
    assert "from mocks import" in generated
    assert "CustomUnset" in generated
    assert "CUSTOM_UNSET" in generated
    # Used in the convenience-function signature and conditional dict.
    assert "Union[Optional[Filter], CustomUnset]=CUSTOM_UNSET" in generated
    assert "is not CUSTOM_UNSET" in generated


def test_unset_override_must_be_paired():
    """Overriding only one of the UNSET type/instance is a config error."""
    import pytest as _pytest

    with _pytest.raises(Exception):
        GeneratorConfig(unset_type_class="mocks.CustomUnset")


def test_funcs_build_variables_conditionally(tmp_path):
    """The generated convenience function defaults optional args to UNSET and only
    adds the ones the caller provided to the variables dict."""
    generated = parse_to_code(_generate(tmp_path, "v2", with_funcs=True))

    # The sentinel is emitted into the module.
    assert "class UnsetType:" in generated
    assert "UNSET = UnsetType()" in generated

    # Optional args default to UNSET and carry UnsetType in their type union.
    assert "filter: Union[Optional[Filter], UnsetType]=UNSET" in generated
    assert "limit: Union[Optional[int], UnsetType]=UNSET" in generated

    # The variables dict is loosely typed and assembled conditionally.
    assert "variables: Dict[str, Any] = {}" in generated
    assert "if filter is not UNSET:" in generated
    assert "variables['filter'] = filter" in generated
    assert "if limit is not UNSET:" in generated
