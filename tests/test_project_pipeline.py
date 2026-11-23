import pytest

from turms.config import ConfigProxy, Extensions, GeneratorConfig
from turms.run import GraphQLProject, generate


@pytest.mark.network
def test_project_pipeline():
    config = GraphQLProject(
        schema="https://countries.trevorblades.com/",
        scalar_definitions={"_Any": "typing.Any"},
        extensions=Extensions(
            turms=GeneratorConfig(
                plugins=[
                    ConfigProxy(type="turms.plugins.enums.EnumsPlugin"),
                    ConfigProxy(type="turms.plugins.inputs.InputsPlugin"),
                    ConfigProxy(type="turms.plugins.objects.ObjectsPlugin"),
                ],
                stylers=[
                    ConfigProxy(type="turms.stylers.default.DefaultStyler"),
                ],
            )
        ),
    )

    generated_ast = generate(config)

    assert generated_ast
