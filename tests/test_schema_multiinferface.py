import ast

import pytest
from tests.utils import build_relative_glob
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url


@pytest.fixture()
def multi_interface_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/multi_interface.graphql")
    )


def test_generation(multi_interface_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        multi_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    print(generated)
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "class Query(BaseModel)" in generated, "No Query was detected"
