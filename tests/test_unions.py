
from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.funcs import (
    FuncsPlugin,
    FuncsPluginConfig,
    FunctionDefinition,
)
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, unit_test_with


def test_nested_input_funcs(union_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/unions/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        union_schema,
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

    unit_test_with(
        generated_ast,
        'Nana(hallo={"__typename": "Foo","forward": "yes"}).hallo.forward',
    )

def test_fields_in_inline_fragment_on_union(union_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/unions/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        union_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )

    unit_test_with(
        generated_ast,
        """
        assert Nana(hallo={'__typename': 'Foo', 'blip': 'A', 'forward': 'yes'}).hallo.blip == 'A'
        assert Nana(hallo={'__typename': 'Bar', 'nana': 1}).hallo.nana == 1
        assert Nana2(hallo={'__typename': 'Baz', 'bloop': 'C'}).hallo.bloop == 'C'
        assert Nana3(hallo={'__typename': 'Baz', 'bloop': 'C'}).hallo.bloop == 'C'
        assert Nana3(hallo={'__typename': 'Bar', 'nana': 1}).hallo.nana == 1
        assert Nana4(hallo={'__typename': 'Bar', 'nana': 1}).hallo.nana == 1
        """,
    )

    

