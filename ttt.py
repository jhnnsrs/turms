import ast

import pytest
from tests.utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.fragments import FragmentsPlugin, FragmentsPluginConfig
from turms.plugins.operations import OperationsPlugin
from turms.stylers.appender import AppenderStyler, AppenderStylerConfig
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.helpers import build_schema_from_glob
from turms.processors.black import BlackProcessor
from turms.processors.isort import IsortProcessor


config = GeneratorConfig(
    documents=build_relative_glob("/documents/arkitekt/**/*.graphql"),
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
    build_schema_from_glob(build_relative_glob("/schemas/arkitekt.graphql")),
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
                            type="mutation",
                            use="tests.mocks.query",
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
with open("sdfsdf.py", "w") as f:
    f.write(generated)

unit_test_with(generated_ast, "WidgetInput(typename='oisnoisn')")
unit_test_with(
    generated_ast, "ReturnPortInput(child=ReturnPortInput(bound=BoundTypeInput.AGENT))"
)
unit_test_with(generated_ast, "SliderWidget()")
unit_test_with(generated_ast, "StringArgPort()")
