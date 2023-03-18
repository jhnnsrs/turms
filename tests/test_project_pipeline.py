
from turms.config import GeneratorConfig, Extensions, ConfigProxy
from turms.run import generate, GraphQLProject


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
                parsers=[ConfigProxy(type="turms.parsers.polyfill.PolyfillParser")],
            )
        ),
    )

    generated_ast = generate(config)

    assert generated_ast
