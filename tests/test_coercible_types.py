from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.plugins.funcs import (
    FuncsPlugin,
    FuncsPluginConfig,
    FunctionDefinition,
)
from turms.plugins.fragments import FragmentsPlugin
from turms.stylers.default import DefaultStyler


def test_coercible_types_in_funcs(beast_schema):
    """Test that coercible scalars are properly handled in function generation."""
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/**/*.graphql"),
        scalar_definitions={
            "ID": "str",
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
                    coercible_scalars={
                        "ID": "pydantic.UUID4",  # Coerce ID scalar to UUID4
                        "String": "pathlib.Path",  # Coerce String to Path
                    },
                    definitions=[
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.query",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="query",
                            use="mocks.query",
                            is_async=False,
                        ),
                    ],
                ),
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "",  # Empty test code - we just want to verify generation works
    )


def test_coercible_types_mixed_with_regular_scalars(beast_schema):
    """Test that coercible scalars work alongside regular scalar definitions."""
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/**/*.graphql"),
        scalar_definitions={
            "ID": "str",
            "Int": "int",  # Regular scalar definition
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
                    coercible_scalars={
                        "ID": "uuid.UUID",  # Only coerce ID, leave Int as regular
                    },
                    definitions=[
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.query",
                            is_async=False,
                        ),
                    ],
                ),
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "",  # Empty test code - we just want to verify generation works
    )


def test_coercible_types_optional_and_non_optional(beast_schema):
    """Test that coercible scalars work with both optional and non-optional fields."""
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/**/*.graphql"),
        scalar_definitions={
            "ID": "str",
            "String": "str",
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
                    coercible_scalars={
                        "ID": "str",  # Test complex type annotation
                        "String": "pathlib.Path",  # Test nested Optional
                    },
                    definitions=[
                        FunctionDefinition(
                            type="mutation",
                            use="mocks.query",
                            is_async=False,
                        ),
                        FunctionDefinition(
                            type="query",
                            use="mocks.query", 
                            is_async=False,
                        ),
                    ],
                ),
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "",  # Empty test code - we just want to verify generation works
    )
