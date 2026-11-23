import pytest
from graphql import GraphQLSchema

from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from .utils import ExecuteError, unit_test_with


@pytest.mark.network
def test_countries_schema(countries_schema: GraphQLSchema) -> None:
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")

    with pytest.raises(ExecuteError):
        unit_test_with(generated_ast, "Country()")


def test_arkitekt_schema(arkitekt_schema: GraphQLSchema) -> None:
    config = GeneratorConfig(
        scalar_definitions={"QString": "str", "Any": "str", "UUID": "pydantic.UUID4"}
    )

    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
