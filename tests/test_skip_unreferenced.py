from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast, parse_asts_to_string
from turms.plugins.enums import EnumsPlugin, EnumsPluginConfig
from turms.plugins.inputs import InputsPlugin, InputsPluginConfig
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.plugins.funcs import (
    FunctionDefinition,
    FuncsPlugin,
    FuncsPluginConfig,
)
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.run import generate_ast


def test_skip_unreferenced(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(config=EnumsPluginConfig(skip_unreferenced=True)),
            InputsPlugin(config=InputsPluginConfig(skip_unreferenced=True)),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    x = parse_asts_to_string(generated_ast)
    assert (
        "StringQueryOperatorInput" not in x
    ), "StringQueryOperatorInput should be skipped"
