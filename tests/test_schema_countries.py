import ast

from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.stylers.default import DefaultStyler
from turms.run import generate_ast
from .utils import unit_test_with


def test_complex_operations(countries_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "class Query(BaseModel)" in generated, "No Query was detected"
