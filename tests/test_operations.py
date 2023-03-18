
from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin, OperationsPluginConfig
from turms.plugins.fragments import FragmentsPlugin
from turms.stylers.default import DefaultStyler
from turms.run import generate_ast


def test_extra_arguments(arkitekt_schema):
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
            OperationsPlugin(
                config=OperationsPluginConfig(
                    subscription_bases=["mocks.ExtraOnOperations"],
                    mutation_bases=["mocks.ExtraOnOperations"],
                    query_bases=["mocks.ExtraOnOperations"],
                    arguments_bases=["mocks.ExtraArguments"],
                )
            ),
        ],
    )

    unit_test_with(
        generated_ast,
        "ReturnPortInput(child=ReturnPortInput(bound=BoundTypeInput.AGENT))",
    )
