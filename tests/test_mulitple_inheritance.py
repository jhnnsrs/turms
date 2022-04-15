import ast

import pytest

from .utils import (
    build_relative_glob,
    unit_test_with,
)
from turms.config import GeneratorConfig
from turms.helpers import build_schema_from_glob
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler


@pytest.fixture()
def multiple_inheritance_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/multiple_inhertiance.graphql")
    )


def test_generation(multiple_inheritance_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        multiple_inheritance_schema,
        stylers=[DefaultStyler()],
        plugins=[
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
