import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url
from .utils import build_relative_glob, unit_test_with
import pydantic


@pytest.fixture()
def builtin_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/builtin.graphql"))


def test_load_projects(builtin_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        builtin_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
