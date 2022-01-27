from turms.run import gen
from turms.compat.funcs import unparse
from ast import parse


def test_config():
    assert 1 == 1, "Test pytest"


def test_unparse():
    instring = """
class TestClass:
    number: int
    """

    x = parse(instring)
    unparse(x)
