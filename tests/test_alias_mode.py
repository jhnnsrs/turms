"""Tests for ``options.alias_mode``.

``alias_mode="single"`` (the default) emits one ``Field(alias=...)``. pydantic
uses it for both validation and serialization, and because a type checker
synthesizes ``__init__`` from the ``alias`` field specifier -- and never reads
``populate_by_name``, which is runtime-only -- the python (snake_case) spelling
does not type-check even though it works.

``alias_mode="split"`` emits ``validation_alias=AliasChoices(python, graphql)``
plus ``serialization_alias=graphql``. Both spellings still validate, the wire
format is byte-identical, and the python spelling now type-checks.
"""

import pytest
from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig, OptionsConfig
from turms.errors import GenerationError
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from .utils import parse_to_code, type_check_with, unit_test_with

schema_sdl = """
input Filter {
    otherMandatory: String!
    plainOptional: String
}

type Country {
    code: String
}

type Query {
    countries(filter: Filter, maxDepth: Int): [Country!]!
}
"""

operation = """
query GetCountries($filter: Filter, $maxDepth: Int) {
  countries(filter: $filter, maxDepth: $maxDepth) {
    code
  }
}
"""


def _generate(tmp_path, alias_mode):
    doc = tmp_path / "ops.graphql"
    doc.write_text(operation)
    config = GeneratorConfig(
        documents=str(tmp_path / "**/*.graphql"),
        options=OptionsConfig(
            enabled=True,
            alias_mode=alias_mode,
            populate_by_name=True,
            types=["input"],
        ),
    )
    return generate_ast(
        config,
        build_ast_schema(parse(schema_sdl)),
        stylers=[DefaultStyler()],
        plugins=[InputsPlugin(), ObjectsPlugin(), OperationsPlugin()],
    )


def test_single_is_the_default(tmp_path):
    generated = parse_to_code(_generate(tmp_path, "single"))
    assert "other_mandatory: str = Field(alias='otherMandatory')" in generated
    assert "AliasChoices" not in generated


def test_split_emits_validation_and_serialization_alias(tmp_path):
    generated = parse_to_code(_generate(tmp_path, "split"))
    assert (
        "other_mandatory: str = Field("
        "validation_alias=AliasChoices('other_mandatory', 'otherMandatory'), "
        "serialization_alias='otherMandatory')"
    ) in generated
    assert "from pydantic import" in generated and "AliasChoices" in generated


def test_split_applies_to_operation_arguments(tmp_path):
    """Arguments is constructed by the generated funcs, so it follows the input
    policy rather than the output one."""
    generated = parse_to_code(_generate(tmp_path, "split"))
    assert (
        "max_depth: int | None = Field("
        "validation_alias=AliasChoices('max_depth', 'maxDepth'), "
        "serialization_alias='maxDepth', default=None)"
    ) in generated


def test_split_leaves_output_types_on_a_single_alias(tmp_path):
    """Output types are parsed from the wire, never constructed by the caller, so
    they keep one plain alias -- and __typename must stay a plain alias because
    pydantic forbids a split alias on a discriminated-union tag."""
    generated = parse_to_code(_generate(tmp_path, "split"))
    assert "Field(alias='__typename'" in generated


@pytest.mark.parametrize("alias_mode", ["single", "split"])
def test_both_spellings_validate_and_wire_format_is_identical(tmp_path, alias_mode):
    unit_test_with(
        _generate(tmp_path, alias_mode),
        """
        by_python_name = Filter(other_mandatory="a")
        by_graphql_name = Filter.model_validate({"otherMandatory": "a"})
        assert by_python_name == by_graphql_name
        assert by_python_name.model_dump(by_alias=True, exclude_unset=True) == {
            "otherMandatory": "a"
        }
        """,
    )


def test_split_makes_the_python_spelling_type_check(tmp_path):
    """The actual point of the feature -- and invisible to a runtime test."""
    probe = """
    Filter(other_mandatory="a")
    """
    single = type_check_with(_generate(tmp_path, "single"), probe)
    if single is None:
        pytest.skip("no pyright-compatible type checker installed")
    split = type_check_with(_generate(tmp_path, "split"), probe)

    assert single, "expected the python spelling to NOT type-check under 'single'"
    assert any("other_mandatory" in message for _, message in single)
    assert not split, f"expected no errors under 'split', got {split}"


def test_split_rejects_the_graphql_spelling_statically(tmp_path):
    """Under split the wire spelling is serialization-only, so passing it as a
    keyword is a type error -- while still working at runtime."""
    diagnostics = type_check_with(
        _generate(tmp_path, "split"), 'Filter(otherMandatory="a")'
    )
    if diagnostics is None:
        pytest.skip("no pyright-compatible type checker installed")
    assert any("otherMandatory" in message for _, message in diagnostics)


discriminated_sdl = """
directive @unionElementOf(
    union: String!
    discriminator: String!
    key: String!
) repeatable on INPUT_OBJECT

input LaserInput @unionElementOf(union: "ElementInput", discriminator: "kind", key: "LASER") {
    kind: String!
    powerLevel: Float
}

input ElementInput {
    kind: String!
}

type Query {
    a(element: ElementInput): String
}
"""

discriminated_operation = """
query A($element: ElementInput) { a(element: $element) }
"""


@pytest.mark.parametrize("alias_mode", ["single", "split"])
def test_discriminator_tag_never_gets_an_alias(tmp_path, alias_mode):
    """pydantic raises ``Alias [...] is not supported in a discriminated union``
    for a non-string alias on a tag field, so the tag must stay bare in both
    modes -- while its siblings still get the mode's aliasing."""
    doc = tmp_path / "ops.graphql"
    doc.write_text(discriminated_operation)
    config = GeneratorConfig(
        documents=str(tmp_path / "**/*.graphql"),
        options=OptionsConfig(enabled=True, alias_mode=alias_mode, types=["input"]),
    )
    generated = parse_to_code(
        generate_ast(
            config,
            build_ast_schema(parse(discriminated_sdl)),
            stylers=[DefaultStyler()],
            plugins=[InputsPlugin(), ObjectsPlugin(), OperationsPlugin()],
        )
    )
    assert "kind: Literal['LASER'] = Field(default='LASER')" in generated
    # the non-tag field still follows the mode
    if alias_mode == "split":
        assert "AliasChoices('power_level', 'powerLevel')" in generated
    else:
        assert "Field(alias='powerLevel'" in generated


def test_styled_discriminator_is_refused(tmp_path):
    """A multi-word discriminator would be emitted under its raw name while the
    ordinary-field loop styles it, so it would be emitted twice -- and could
    never carry the alias that would reconcile them."""
    sdl = discriminated_sdl.replace('discriminator: "kind"', 'discriminator: "myKind"')
    sdl = sdl.replace("input LaserInput", "input LaserInput").replace(
        "    kind: String!\n    powerLevel: Float", "    myKind: String!\n    powerLevel: Float"
    )
    doc = tmp_path / "ops.graphql"
    doc.write_text(discriminated_operation)
    config = GeneratorConfig(
        documents=str(tmp_path / "**/*.graphql"),
        options=OptionsConfig(enabled=True, alias_mode="split", types=["input"]),
    )
    with pytest.raises(GenerationError, match="not supported|forbids|styled"):
        generate_ast(
            config,
            build_ast_schema(parse(sdl)),
            stylers=[DefaultStyler()],
            plugins=[InputsPlugin(), ObjectsPlugin(), OperationsPlugin()],
        )


def test_alias_mode_is_independent_of_enabled_and_types(tmp_path):
    """``alias_mode`` chooses how a Field specifier spells its alias; ``enabled``
    and ``types`` choose which models get a generated ``model_config``. Gating
    the first on the second would be wrong -- ``Arguments`` is OPERATION-scoped
    but must follow the INPUT policy -- so the independence is the contract, not
    an accident of the default config."""
    doc = tmp_path / "ops.graphql"
    doc.write_text(operation)
    config = GeneratorConfig(
        documents=str(tmp_path / "**/*.graphql"),
        # options entirely off, and scoped to a type that is not INPUT
        options=OptionsConfig(enabled=False, alias_mode="split", types=["fragment"]),
    )
    generated = parse_to_code(
        generate_ast(
            config,
            build_ast_schema(parse(schema_sdl)),
            stylers=[DefaultStyler()],
            plugins=[InputsPlugin(), ObjectsPlugin(), OperationsPlugin()],
        )
    )
    assert "AliasChoices('other_mandatory', 'otherMandatory')" in generated
    assert "AliasChoices('max_depth', 'maxDepth')" in generated
    # ...and no model_config was emitted, since options.enabled is False
    assert "model_config = ConfigDict(" not in generated


def test_generated_enums_have_strenum_semantics(tmp_path):
    """``class X(str, Enum)`` inherits ``Enum.__str__``, so ``str(X.A)`` is
    "X.A". Generated enums restore ``str.__str__`` so a value that reaches a log
    line or an f-string reads as the wire value -- which is what makes dropping
    ``use_enum_values`` behaviourally transparent."""
    from turms.plugins.enums import EnumsPlugin

    doc = tmp_path / "ops.graphql"
    doc.write_text("query GetCountries { countries { code kind } }")
    config = GeneratorConfig(documents=str(tmp_path / "**/*.graphql"))
    generated_ast = generate_ast(
        config,
        build_ast_schema(
            parse(
                """
                enum Kind { LASER }
                type Country { code: String, kind: Kind }
                type Query { countries: [Country!]! }
                """
            )
        ),
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), ObjectsPlugin(), OperationsPlugin()],
    )
    assert "__str__ = str.__str__" in parse_to_code(generated_ast)
    unit_test_with(
        generated_ast,
        """
        assert str(Kind.LASER) == "LASER"
        assert f"{Kind.LASER}" == "LASER"
        assert Kind.LASER == "LASER"
        assert isinstance(Kind.LASER, str)
        """,
    )
