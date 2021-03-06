import ast

import pytest
from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob

@pytest.fixture()
def mro_test_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/mro.graphql")
    )


def test_generation(mro_test_schema):
    config = GeneratorConfig(
    )

    generated_ast = generate_ast(
        config,
        mro_test_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )
    unit_test_with(generated_ast, "ThisWorks(foo='hallo', bar='good')")