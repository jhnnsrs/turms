import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url
from .utils import build_relative_glob, unit_test_with, ExecuteError
import pydantic


@pytest.fixture()
def countries_schema():
    return build_schema_from_introspect_url("https://countries.trevorblades.com/")


@pytest.fixture()
def arkitekt_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/arkitekt.graphql"))


def test_countries_schema(countries_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            StrawberryPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")

    with pytest.raises(ExecuteError):
        unit_test_with(generated_ast, "Country()")


def test_arkitekt_schema(arkitekt_schema):
    config = GeneratorConfig(
        scalar_definitions={"QString": "str", "Any": "str", "UUID": "pydantic.UUID4"}
    )

    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            StrawberryPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
