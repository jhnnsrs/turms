import ast
from turms.config import GeneratorConfig
from turms.run import gen, generate_ast
from turms.compat.funcs import unparse
from graphql.language import parse
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.stylers.snake import SnakeNodeName


def test_config():
    assert 1 == 1, "Test pytest"


def test_unparse():
    """Needs to be tested for compliance with older python versions via astunparse"""
    instring = """
class TestClass:
    number: int
    """

    x = ast.parse(instring)
    unparse(x)


def test_small():
    schema = parse(
        """type Query {
        hello(orderBy: HelloWorldOrder! = ASC, filter: HelloWorldFilter,
            first: Int, last: Int, before: String, after: String): [World!]!
        }

        enum HelloWorldOrder {
        ASC
        DESC
        }

        input HelloWorldFilter {
        search: String!
        }

        type World {
        message: String!
        }
    """
    )
    config = GeneratorConfig()
    generated_ast = generate_ast(
        config, dsl=schema, plugins=[EnumsPlugin(), InputsPlugin()]
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "class HelloWorldOrder(str, Enum):" in generated, "EnumPlugin not working"


def test_small():
    schema = parse(
        """type Query {
        hello(orderBy: HelloWorldOrder! = ASC, filter: HelloWorldFilter,
            first: Int, last: Int, before: String, after: String): [World!]!
        }

        enum HelloWorldOrder {
        ASC
        DESC
        }

        input HelloWorldFilter {
        searchMassimo: String!
        }

        type World {
        message: String!
        }
    """
    )
    config = GeneratorConfig()
    generated_ast = generate_ast(
        config, dsl=schema, plugins=[EnumsPlugin(), InputsPlugin()]
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "class HelloWorldOrder(str, Enum):" in generated, "EnumPlugin not working"


def test_snake_case_styler():
    schema = parse(
        """type Query {
        hello(orderBy: HelloWorldOrder! = ASC, filter: HelloWorldFilter,
            first: Int, last: Int, before: String, after: String): [World!]!
        }

        enum HelloWorldOrder {
        ASC
        DESC
        }

        input HelloWorldFilter {
        searchMassimo: String!
        }

        type World {
        message: String!
        }
    """
    )
    config = GeneratorConfig()
    generated_ast = generate_ast(
        config,
        dsl=schema,
        stylers=[SnakeNodeName()],
        plugins=[EnumsPlugin(), InputsPlugin()],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = unparse(ast.fix_missing_locations(md))
    assert "from enum import Enum" in generated, "EnumPlugin not working"
    assert "search_massimo: str" in generated, "Snake Casing not Working"
    assert (
        """search_massimo: str = Field(alias='searchMassimo')""" in generated
    ), "Automated Field aliasing not working"
