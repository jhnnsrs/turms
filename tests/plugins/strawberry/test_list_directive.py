
from ...utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.plugins.funcs import (
    FunctionDefinition,
    FuncsPlugin,
    FuncsPluginConfig,
)
from turms.plugins.strawberry import StrawberryPlugin
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.run import generate_ast


def test_list_directive_funcs(directive_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/directives/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        directive_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
    )

    unit_test_with(
        generated_ast,
        ""
    )
