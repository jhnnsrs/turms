import ast
from tests.utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.helpers import build_schema_from_glob


config = GeneratorConfig(
    documents=build_relative_glob("/documents/multi_interface/**/*.graphql"),
    scalar_definitions={
        "uuid": "str",
        "Callback": "str",
        "Any": "typing.Any",
        "QString": "str",
        "UUID": "pydantic.UUID4",
    },
)
generated_ast = generate_ast(
    config,
    build_schema_from_glob(build_relative_glob("/schemas/multi_interface.graphql")),
    stylers=[
        CapitalizeStyler(),
        SnakeCaseStyler(),
    ],
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
                            type="query",
                            use="tests.mocks.query",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="tests.mocks.query",
                            is_async=True,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="tests.mocks.query",
                            is_async=False,
                        ),
                    ]
                ),
            ),
        ),
    ],
)

md = ast.Module(body=generated_ast, type_ignores=[])
generated = ast.unparse(ast.fix_missing_locations(md))
with open("generated.py", "w") as f:
    f.write(generated)
