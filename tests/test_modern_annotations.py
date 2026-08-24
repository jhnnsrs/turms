"""Tests for the modern type annotation style.

With `type_annotation_style` set to `modern` (or `auto` on a recent enough
`min_python_version`) the generated annotations are spelled with PEP 585 builtin
generics and PEP 604 unions -- `list[str] | None` instead of
`Optional[List[str]]` -- and the typing imports that became obsolete are pruned.
"""


import pytest
from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.input_funcs import InputFuncsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.default import DefaultStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, parse_to_code, unit_test_with

schema_sdl = """
scalar GenericScalar

input FilterInput {
    limit: Int = 10
    tags: [String!]
    nested: FilterInput
}

type Country {
    code: String
    name: String!
    tags: [String]
    friends: [Country!]
    extra: GenericScalar
}

type Query {
    countries(filter: FilterInput): [Country!]!
}
"""


def generate(**config_kwargs):
    config = GeneratorConfig(
        scalar_definitions={"GenericScalar": "typing.Dict"}, **config_kwargs
    )
    return generate_ast(
        config,
        build_ast_schema(parse(schema_sdl)),
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), ObjectsPlugin()],
    )


# --------------------------------------------------------------------------- #
# config resolution
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "style,version,builtin_generics,union_operator",
    [
        ("legacy", "3.13", False, False),
        # `modern` opts into every modern spelling regardless of the declared floor
        ("modern", "3.9", True, True),
        ("auto", "3.9", True, False),
        ("auto", "3.10", True, True),
        ("auto", "3.12", True, True),
    ],
)
def test_style_resolution(style, version, builtin_generics, union_operator):
    config = GeneratorConfig(type_annotation_style=style, min_python_version=version)
    assert config.use_builtin_generics is builtin_generics
    assert config.use_union_operator is union_operator


def test_defaults_are_auto():
    """`auto` on the default floor (3.10, matching turms' own requires-python)
    means new projects get the modern spelling without configuring anything."""
    config = GeneratorConfig()
    assert config.type_annotation_style == "auto"
    assert config.min_python_version == "3.10"
    assert config.use_builtin_generics is True
    assert config.use_union_operator is True


# --------------------------------------------------------------------------- #
# generated output
# --------------------------------------------------------------------------- #


def test_legacy_output_unchanged():
    """`legacy` still produces exactly the classic typing spelling."""
    code = parse_to_code(generate(type_annotation_style="legacy"))
    assert "Optional[List[str]]" in code
    assert "Optional[str]" in code
    assert "Optional['Country']" in code or "Optional[List['Country']]" in code
    assert "Dict" in code
    assert "|" not in code


def test_modern_output():
    # the default (auto on 3.10) has to agree with an explicit `modern`
    assert parse_to_code(generate()) == parse_to_code(
        generate(type_annotation_style="modern")
    )
    code = parse_to_code(generate(type_annotation_style="modern"))
    assert "tags: list[str] | None" in code
    assert "code: str | None" in code
    assert "name: str" in code
    assert "countries: list[Country]" in code
    # the GenericScalar scalar points at typing.Dict, which PEP 585 replaces
    assert "extra: dict | None" in code
    assert "Optional" not in code
    assert "List[" not in code


def test_modern_prunes_typing_imports():
    code = parse_to_code(generate(type_annotation_style="modern"))
    typing_imports = [
        line for line in code.splitlines() if line.startswith("from typing import")
    ]
    assert typing_imports, "Literal is still needed and has no modern equivalent"
    for line in typing_imports:
        assert "Optional" not in line
        assert "List" not in line
        assert "Dict" not in line


def test_builtin_generics_only():
    """python 3.9 gets PEP 585 but not PEP 604."""
    generated_ast = generate(type_annotation_style="auto", min_python_version="3.9")
    code = parse_to_code(generated_ast)
    assert "tags: Optional[list[str]]" in code
    assert "List[" not in code
    assert "Optional[" in code
    unit_test_with(generated_ast, "")


def test_forward_references_become_string_annotations():
    """`'Country' | None` is a TypeError at class creation, so a union with a
    forward reference has to be emitted as a whole string annotation."""
    code = parse_to_code(generate(type_annotation_style="modern"))
    assert "nested: 'FilterInput | None'" in code
    # a forward ref nested inside a subscript stays a plain subscript
    assert "friends: list['Country'] | None" in code
    unit_test_with(generate(type_annotation_style="modern"), "")


def test_scalar_definition_from_other_module_is_not_rewritten():
    """Only names that really came from `typing` may become builtins."""
    config = GeneratorConfig(
        type_annotation_style="modern",
        scalar_definitions={"GenericScalar": "mocks.Dict"},
    )
    code = parse_to_code(
        generate_ast(
            config,
            build_ast_schema(parse(schema_sdl)),
            stylers=[DefaultStyler()],
            plugins=[EnumsPlugin(), InputsPlugin(), ObjectsPlugin()],
        )
    )
    assert "from mocks import Dict" in code
    assert "extra: Dict | None" in code


# --------------------------------------------------------------------------- #
# the generated code has to actually run
# --------------------------------------------------------------------------- #

MODERN = {"type_annotation_style": "modern"}

FUNCS = FuncsPlugin(
    config=FuncsPluginConfig(
        definitions=[
            FunctionDefinition(type="query", use="mocks.query", is_async=False),
            FunctionDefinition(type="query", use="mocks.aquery", is_async=True),
            FunctionDefinition(type="mutation", use="mocks.query", is_async=False),
            FunctionDefinition(
                type="subscription", use="mocks.subscribe", is_async=False
            ),
        ]
    )
)


def test_modern_arkitekt_operations(arkitekt_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/arkitekt/**/*.graphql"),
        scalar_definitions={
            "uuid": "str",
            "Callback": "str",
            "Any": "typing.Any",
            "QString": "str",
            "UUID": "pydantic.UUID4",
        },
        **MODERN,
    )
    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FUNCS,
        ],
    )
    code = parse_to_code(generated_ast)

    # Function signatures are evaluated eagerly at `def` time -- there is no
    # model_rebuild() to resolve a string annotation later -- so no signature
    # may end up carrying one.
    signatures = [
        line
        for line in code.splitlines()
        if line.lstrip().startswith(("def ", "async def "))
    ]
    modern = [line for line in signatures if "| None" in line or "UnsetType" in line]
    assert modern, "the funcs plugin should emit unions in its signatures"
    for line in signatures:
        parameters = line.split("->")[0]
        assert "'" not in parameters and '"' not in parameters
        assert "Optional[" not in line and "Union[" not in line and "List[" not in line

    assert "dict[str, Any]" in code

    unit_test_with(generated_ast, "")


def test_modern_multi_interface(multi_interface_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/multi_interface/**/*.graphql"),
        **MODERN,
    )
    generated_ast = generate_ast(
        config,
        multi_interface_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )
    unit_test_with(generated_ast, "")


def test_modern_unions(union_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/unions/**/*.graphql"), **MODERN
    )
    generated_ast = generate_ast(
        config,
        union_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )
    code = parse_to_code(generated_ast)
    assert "Union[" not in code
    unit_test_with(generated_ast, "")


def test_modern_nested_inputs(nested_input_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/nested_inputs/**/*.graphql"), **MODERN
    )
    generated_ast = generate_ast(
        config,
        nested_input_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )
    unit_test_with(generated_ast, "")


def test_modern_oneof_input_funcs(oneof_schema):
    config = GeneratorConfig(**MODERN)
    generated_ast = generate_ast(
        config,
        oneof_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), InputFuncsPlugin()],
    )
    unit_test_with(generated_ast, "")


def test_modern_forward_reference_to_interface(forward_reference_to_interface_schema):
    generated_ast = generate_ast(
        GeneratorConfig(**MODERN),
        forward_reference_to_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[ObjectsPlugin()],
    )
    unit_test_with(generated_ast, "")


def test_modern_multiple_forward_references(multiple_forward_references_schema):
    generated_ast = generate_ast(
        GeneratorConfig(**MODERN),
        multiple_forward_references_schema,
        stylers=[DefaultStyler()],
        plugins=[ObjectsPlugin()],
    )
    unit_test_with(generated_ast, "")


def test_modern_mro(mro_test_schema):
    generated_ast = generate_ast(
        GeneratorConfig(**MODERN),
        mro_test_schema,
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), ObjectsPlugin()],
    )
    unit_test_with(generated_ast, "ThisWorks(foo='hallo', bar='good')")


def test_modern_keyword(keyword_schema):
    generated_ast = generate_ast(
        GeneratorConfig(**MODERN),
        keyword_schema,
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), ObjectsPlugin()],
    )
    unit_test_with(generated_ast, "")


def test_modern_strawberry(arkitekt_schema):
    """Strawberry reads the annotations itself, so it has to cope with them too."""
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        },
        **MODERN,
    )
    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[DefaultStyler()],
        plugins=[StrawberryPlugin()],
        skip_forwards=True,
    )
    unit_test_with(generated_ast, "")


# --------------------------------------------------------------------------- #
# docstrings
# --------------------------------------------------------------------------- #


def test_modern_docstring_labels(arkitekt_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/arkitekt/**/*.graphql"),
        scalar_definitions={
            "uuid": "str",
            "Callback": "str",
            "Any": "typing.Any",
            "QString": "str",
            "UUID": "pydantic.UUID4",
        },
        **MODERN,
    )
    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FUNCS,
        ],
    )
    code = parse_to_code(generated_ast)
    assert "Optional[List[" not in code
    assert "Optional[" not in code
    assert "| None, optional)" in code
