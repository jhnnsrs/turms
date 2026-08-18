import ast

import pytest
from .utils import build_relative_glob, unit_test_with, ExecuteError
from pydantic import ValidationError

from turms.config import GeneratorConfig, OptionsConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.default import DefaultStyler


def test_allow_population_by_field_name(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            allow_population_by_field_name=True,
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(
        generated_ast,
        "Countries(countries=[CountriesCountries(emoji_u='soinsisn',phone='sdf', capital='dfsdf')]).countries[0].emoji_u",
    )
    assert "from enum import Enum" in generated, "EnumPlugin not working"


def test_extra_forbid(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="forbid",
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    ast.unparse(ast.fix_missing_locations(md))
    with pytest.raises(ExecuteError):
        unit_test_with(
            generated_ast,
            "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf', hundi='soinsoin')]).countries[0].emoji_u",
        )


def test_extra_allow(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="allow",
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(
        generated_ast,
        "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf', hundi='soinsoin')]).countries[0].emoji_u",
    )


def test_from_attributes(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            from_attributes=True,
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(
        generated_ast,
        "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf')]).countries[0].emoji_u",
    )


@pytest.mark.parametrize(
    "removed_option, replacement",
    [("orm_mode", "from_attributes"), ("allow_mutation", "freeze")],
)
def test_pydantic_v1_options_are_rejected(removed_option, replacement):
    """The pydantic v1 option spellings name their replacement instead of
    failing as an anonymous 'extra inputs are not permitted'."""
    with pytest.raises(ValidationError, match=replacement):
        OptionsConfig(enabled=True, **{removed_option: True})


def test_pydantic_v1_target_is_rejected():
    """pydantic_version: v2 still loads (it is a no-op); v1 is an error."""
    assert GeneratorConfig(pydantic_version="v2").pydantic_version == "v2"
    with pytest.raises(ValidationError, match="pydantic v2"):
        GeneratorConfig(pydantic_version="v1")


def test_generated_options_module_imports_without_warnings(countries_schema):
    """Every option the OptionsConfig can emit must be a config key pydantic v2
    actually accepts -- a v1 leftover surfaces as a UserWarning on import."""
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="forbid",
            use_enum_values=True,
            validate_assignment=True,
            allow_population_by_field_name=True,
            from_attributes=True,
        ),
    )
    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )
    unit_test_with(generated_ast, "", strict_warnings=True)
