import ast
from graphql import parse, build_ast_schema
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.stylers.snake_case import SnakeCaseStyler
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from .utils import unit_test_with

inputs = '''
input X {
    mandatory: String!
    otherMandatory: String!
    optional: String
    otherOptional: String
}
'''


expected = '''class X(BaseModel):
    mandatory: str
    other_mandatory: str = Field(alias='otherMandatory')
    optional: Optional[str] = None
    other_optional: Optional[str] = Field(alias='otherOptional', default=None)'''


def test_generates_schema(snapshot):
    config = GeneratorConfig()

    schema = build_ast_schema(parse(inputs))

    generated_ast = generate_ast(
        config,
        schema,
        stylers=[SnakeCaseStyler()],
        plugins=[
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, '')

    without_imports = [node for node in generated_ast if not isinstance(node, ast.ImportFrom)]
    md = ast.Module(body=without_imports, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert generated == expected
