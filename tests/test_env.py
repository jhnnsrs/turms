import ast
import json

import pytest
from turms.config import GeneratorConfig
from turms.run import gen, generate_ast
from turms.compat.funcs import unparse
from graphql.language import parse
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operation import OperationsPlugin
from turms.stylers.snake import SnakeNodeName
from turms.stylers.capitalize import Capitalizer
from turms.helpers import build_schema_from_glob
from turms.processor.black import BlackProcessor
from turms.processor.isort import IsortProcessor
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


def test_env_complex(arkitekt_schema, monkeypatch):

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
        stylers=[Capitalizer(), SnakeNodeName()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = unparse(ast.fix_missing_locations(md))

    for processor in [
        IsortProcessor(),
        BlackProcessor(),
    ]:
        generated = processor.run(generated)
