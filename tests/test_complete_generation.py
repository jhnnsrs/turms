import ast

import pytest
from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.helpers import build_schema_from_glob
from turms.processors.black import BlackProcessor
from turms.processors.isort import IsortProcessor


@pytest.fixture()
def hello_world_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/helloworld.graphql"))


@pytest.fixture()
def beast_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/beasts.graphql"))


@pytest.fixture()
def arkitekt_schema():
    return build_schema_from_glob(build_relative_glob("/schemas/arkitekt.graphql"))


def test_unparse():
    """Needs to be tested for compliance with older python versions via astunparse"""
    instring = """
class TestClass:
    number: int
    """

    x = ast.parse(instring)
    ast.alias(x)


def test_small(hello_world_schema):

    config = GeneratorConfig()
    generated_ast = generate_ast(
        config, hello_world_schema, plugins=[EnumsPlugin(), InputsPlugin()]
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "class HelloWorldOrder(str, Enum):" in generated, "EnumPlugin not working"


def test_snake_case_styler(hello_world_schema):
    config = GeneratorConfig()
    generated_ast = generate_ast(
        config,
        hello_world_schema,
        stylers=[SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "search_massimo: str" in generated, "Snake Casing not Working"
    assert (
        """search_massimo: str = Field(alias='searchMassimo')""" in generated
    ), "Automated Field aliasing not working"




def test_beast_styler(beast_schema):
    config = GeneratorConfig()
    generated_ast = generate_ast(
        config,
        beast_schema,
        stylers=[SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"


def test_beast_operations(beast_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/*.graphql")
    )
    generated_ast = generate_ast(
        config,
        beast_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "class Get_beasts(BaseModel):" in generated, "OpertiationsPlugin not working"
    assert "common_name: Optional[str]" in generated, "SnakeNodeName not working"


def test_arkitekt_operations(arkitekt_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/arkitekt/**/*.graphql"),
        scalar_definitions={
            "uuid": "str",
            "Callback": "str",
            "Any": "typing.Any",
            "QString": "str",
        },
    )
    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(generated_ast,"Node(name='karl',package='inter', interface='x', description='nanana', type=NodeTypeInput.GENERATOR, id='dd')")
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert (
        "class Create_template(BaseModel):" in generated
    ), "OperationsPlugin not working"


def test_black_complex(arkitekt_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/arkitekt/**/*.graphql"),
        scalar_definitions={
            "uuid": "str",
            "Callback": "str",
            "Any": "typing.Any",
            "QString": "str",
        },
    )
    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))

    for processor in [
        IsortProcessor(),
        BlackProcessor(),
    ]:
        generated = processor.run(generated)
