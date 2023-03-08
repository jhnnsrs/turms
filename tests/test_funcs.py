import ast

import pytest
from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.plugins.funcs import (
    Arg,
    FuncsPlugin,
    FuncsPluginConfig,
    FunctionDefinition,
    Kwarg,
)
from turms.plugins.fragments import FragmentsPlugin
from turms.stylers.default import DefaultStyler
from turms.run import generate_ast, build_schema_from_schema_type


def test_arkitekt_schema(arkitekt_schema):
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
        arkitekt_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=True,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.aquery",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.aquery",
                            is_async=True,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="mocks.subscribe",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="mocks.asubscribe",
                            is_async=True,
                        ),
                    ]
                ),
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "ReturnPortInput(child=ReturnPortInput(bound=BoundTypeInput.AGENT))",
    )


def test_beasts_schema(beast_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/**/*.graphql"),
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
        beast_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=True,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.aquery",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.aquery",
                            is_async=True,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="mocks.subscribe",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="mocks.asubscribe",
                            is_async=True,
                        ),
                    ]
                ),
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "",
    )


def test_extra_args(beast_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/**/*.graphql"),
    )

    extra_args = [
        Arg(
            key="client",
            type="mocks.ExtraArg",
            description="An Extra Arg",
        )
    ]

    extra_kwargs = [
        Kwarg(
            key="extra",
            type="int",
            description="An Extra Arg",
            default=5,
        )
    ]

    generated_ast = generate_ast(
        config,
        beast_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=False,
                            extra_args=extra_args,
                            extra_kwargs=extra_kwargs,
                        ),
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=True,
                            extra_args=extra_args,
                            extra_kwargs=extra_kwargs,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.aquery",
                            is_async=False,
                            extra_args=extra_args,
                            extra_kwargs=extra_kwargs,
                        ),
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.aquery",
                            is_async=True,
                            extra_args=extra_args,
                            extra_kwargs=extra_kwargs,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="mocks.subscribe",
                            is_async=False,
                            extra_args=extra_args,
                            extra_kwargs=extra_kwargs,
                        ),
                        FunctionDefinition(
                            type="subscription",
                            use="mocks.asubscribe",
                            is_async=True,
                            extra_args=extra_args,
                            extra_kwargs=extra_kwargs,
                        ),
                    ]
                ),
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "",
    )
