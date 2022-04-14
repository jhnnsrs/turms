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
def keyword_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/keyword.graphql"))


def test_keyword_transpiling(keyword_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        keyword_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
