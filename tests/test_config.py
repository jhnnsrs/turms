import ast

import pytest
from .utils import build_relative_glob, unit_test_with, ExecuteError
from turms.config import GeneratorConfig, OptionsConfig
from turms.plugins.funcs import (
    FunctionDefinition,
    FuncsPlugin,
    FuncsPluginConfig,
)
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_introspect_url


@pytest.fixture()
def countries_schema():
    return build_schema_from_introspect_url("https://countries.trevorblades.com/")


def test_allow_population_by_field_name(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            allow_population_by_field_name=True,
        )
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
    unit_test_with(generated_ast, "Countries(countries=[CountriesCountries(emoji_u='soinsisn',phone='sdf', capital='dfsdf')]).countries[0].emoji_u")
    assert "from enum import Enum" in generated, "EnumPlugin not working"


def test_extra_forbid(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="forbid",
        )
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
    with pytest.raises(ExecuteError):
        unit_test_with(generated_ast, "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf', hundi='soinsoin')]).countries[0].emoji_u")

def test_extra_allow(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="allow",
        )
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
    unit_test_with(generated_ast, "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf', hundi='soinsoin')]).countries[0].emoji_u")


def test_orm_mode(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            orm_mode=True,
        )
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
    unit_test_with(generated_ast, "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf')]).countries[0].emoji_u")