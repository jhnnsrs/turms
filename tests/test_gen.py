from turms.run import gen
from turms.compat.funcs import unparse
from ast import parse


def test_config():
    assert 1 == 1, "Test pytest"


def test_unparse():
    """Needs to be tested for compliance with older python versions via astunparse"""
    instring = """
class TestClass:
    number: int
    """

    x = parse(instring)
    unparse(x)


def test_gen():
    gen("graphql.config.yaml")
