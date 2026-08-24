
from .utils import build_relative_glob, unit_test_with
from graphql import OperationDefinitionNode, Source, parse

from turms.utils import inspect_operation_for_documentation
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
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.run import generate_ast


def test_documentatoin(nested_input_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/documentation/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        nested_input_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
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
                    ]
                ),
            ),
        ],
    )

    unit_test_with(generated_ast, "")


def test_default_input_funcs(nested_input_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/inputs_default/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        nested_input_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
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
                    ]
                ),
            ),
        ],
    )

    unit_test_with(generated_ast, "")


def test_documentation_above_an_operation_keeps_the_whole_block():
    """A `#` block above an operation is its docstring, all of it.

    graphql-core sets the operation's ``loc.start`` to the *last* preceding comment token
    rather than to the `query`/`mutation` keyword, so slicing forward from that line kept
    only the block's final line and dropped everything above it. Comments *inside* the
    operation body -- the form the fixture below also covers -- were unaffected, which is
    why this went unnoticed.
    """
    path = build_relative_glob("/documents/documentation/test.graphql")
    with open(path) as file:
        source = Source(file.read(), "test.graphql")

    docs = {
        definition.name.value: inspect_operation_for_documentation(definition)
        for definition in parse(source).definitions
        if isinstance(definition, OperationDefinitionNode)
    }

    assert docs["commentedAbove"] == (
        " A comment block above the operation documents it too, and every line of it counts.\n"
        " graphql-core puts the operation's `loc.start` on the last of these lines, so a naive\n"
        " slice forward from there keeps only this sentence and silently drops the two above."
    )
    # The in-body form still works, and an operation with no comment still gets nothing.
    assert docs["createBeast"] == " Testing the documentatoin ability"
    assert docs["createBeastss"] is None
