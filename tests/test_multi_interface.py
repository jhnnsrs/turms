import ast

import pytest
from turms.config import GeneratorConfig
from turms.helpers import build_schema_from_glob
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob


@pytest.fixture()
def multi_interface_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/multi_interface.graphql")
    )


def test_multi_interface_funcs(multi_interface_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/multi_interface/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        multi_interface_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FuncsPlugin(
                config=FuncsPluginConfig(
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
    generated = ast.unparse(ast.fix_missing_locations(md))
