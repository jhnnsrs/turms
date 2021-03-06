import ast

import pytest

from .utils import (
    build_relative_glob,
    unit_test_with,
)
from turms.config import GeneratorConfig
from turms.helpers import build_schema_from_glob
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler


@pytest.fixture()
def forward_reference_to_interface_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/forward_reference_to_interface.graphql")
    )


def test_generation(forward_reference_to_interface_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        forward_reference_to_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
