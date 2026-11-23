from graphql import GraphQLSchema

from turms.config import GeneratorConfig
from turms.plugins.strawberry import StrawberryPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from ...utils import build_relative_glob, unit_test_with


def test_list_directive_funcs(directive_schema: GraphQLSchema) -> None:
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

    unit_test_with(generated_ast, "")
