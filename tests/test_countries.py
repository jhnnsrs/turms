import ast

import pytest
from turms.config import GeneratorConfig
from turms.plugins.funcs import (
    FunctionDefinition,
    OperationsFuncPlugin,
    OperationsFuncPluginConfig,
)
from turms.run import gen, generate_ast
from turms.compat.funcs import unparse
from graphql.language import parse
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operation import OperationsPlugin
from turms.stylers.snake import SnakeNodeName
from turms.stylers.default import DefaultStyler
from turms.stylers.capitalize import Capitalizer
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url
from turms.processor.black import BlackProcessor
from turms.processor.isort import IsortProcessor


@pytest.fixture()
def countries_schema():
    return build_schema_from_introspect_url("https://countries.trevorblades.com/")


def test_complex_operations(countries_schema):
    config = GeneratorConfig(
        documents="tests/documents/countries/**.graphql",
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
            OperationsFuncPlugin(
                config=OperationsFuncPluginConfig(
                    definitions=(
                        [
                            FunctionDefinition(
                                type="query",
                                use="test.func",
                                is_async=False,
                            )
                        ]
                    )
                ),
            ),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = unparse(ast.fix_missing_locations(md))
    print(generated)
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert (
        "def countries() -> List[CountriesCountries]:" in generated
    ), "Collapse not working"
