import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import gen, generate_ast
from turms.compat.funcs import unparse
from graphql.language import parse
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operation import OperationsPlugin
from turms.plugins.funcs import (
    FunctionDefinition,
    OperationsFuncPlugin,
    OperationsFuncPluginConfig,
)
from turms.stylers.snake import SnakeNodeName
from turms.stylers.capitalize import Capitalizer
from turms.helpers import build_schema_from_glob
from turms.processor.black import BlackProcessor
from turms.processor.isort import IsortProcessor


@pytest.fixture()
def nested_input_schema():
    return build_schema_from_glob("tests/schemas/nested_inputs.graphql")


def test_nested_input_funcs(nested_input_schema):
    config = GeneratorConfig(
        documents="tests/documents/nested_inputs/*.graphql",
    )
    generated_ast = generate_ast(
        config,
        nested_input_schema,
        stylers=[Capitalizer(), SnakeNodeName()],
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
                                type="mutation",
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


def test_default_input_funcs(nested_input_schema):
    config = GeneratorConfig(
        documents="tests/documents/inputs_default/*.graphql",
    )
    generated_ast = generate_ast(
        config,
        nested_input_schema,
        stylers=[Capitalizer(), SnakeNodeName()],
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
                                type="mutation",
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
