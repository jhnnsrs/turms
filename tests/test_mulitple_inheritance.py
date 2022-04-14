import ast

import pytest

from tests.utils import build_relative_glob, generated_module_is_executable
from turms.config import GeneratorConfig
from turms.helpers import build_schema_from_glob
from turms.plugins.objects import ObjectsPlugin
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

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert generated_module_is_executable(generated)
