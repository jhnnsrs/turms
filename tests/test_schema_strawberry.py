import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url
from .utils import build_relative_glob, unit_test_with, ExecuteError, parse_to_code
import pydantic


@pytest.fixture()
def countries_schema():
    return build_schema_from_introspect_url("https://countries.trevorblades.com/")


@pytest.fixture()
def arkitekt_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/arkitekt.graphql"))


@pytest.fixture()
def multi_interface_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/multi_interface.graphql")
    )


@pytest.fixture()
def schema_directive_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/directive.graphql"))


@pytest.fixture()
def scalar_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/scalars.graphql"))


def test_countries_schema(countries_schema):
    config = GeneratorConfig(scalar_definitions={"_Any": "typing.Any"})

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_arkitekt_schema(arkitekt_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_multiple_interface(multi_interface_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        multi_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_schema_directive_generation(schema_directive_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        schema_directive_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_custom_scalar_generation(scalar_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        scalar_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")
