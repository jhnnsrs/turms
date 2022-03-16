import ast
import json

import pytest
from turms.config import GeneratorConfig
from turms.run import gen, generate_ast
from graphql.language import parse
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.helpers import build_schema_from_glob
from turms.processors.black import BlackProcessor
from turms.processors.isort import IsortProcessor
from turms.parsers.polyfill import PolyfillParser, PolyfillPluginConfig
import os


@pytest.fixture()
def hello_world_schema():
    return build_schema_from_glob("tests/schemas/helloworld.graphql")


@pytest.fixture()
def arkitekt_schema():
    return build_schema_from_glob("tests/schemas/arkitekt.graphql")


def test_small(hello_world_schema, monkeypatch):

    monkeypatch.setenv("TURMS_DOMAIN", "test_domain")

    config = GeneratorConfig()

    assert config.domain == "test_domain"


def test_polyfill_seven(arkitekt_schema, monkeypatch):

    monkeypatch.setenv(
        "TURMS_SCALAR_DEFINITIONS",
        json.dumps(
            {
                "Callback": "str",
                "Any": "typing.Any",
                "QString": "str",
            },
        ),
    )

    monkeypatch.setenv("TURMS_DOCUMENTS", "tests/documents/arkitekt/**/*.graphql")

    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )

    for parser in [PolyfillParser(config=PolyfillPluginConfig(python_version="3.7"))]:
        generated_ast = parser.parse_ast(generated_ast)

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert "from typing_extensions import Literal" in generated
