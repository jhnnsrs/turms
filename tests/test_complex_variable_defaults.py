from graphql import parse

from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler
from turms.utils import parse_value_node

from .utils import build_relative_glob, unit_test_with


def _defaults(query: str):
    doc = parse(query)
    return {
        v.variable.name.value: parse_value_node(v.default_value)
        for v in doc.definitions[0].variable_definitions
    }


def test_parse_value_node_handles_composite_defaults():
    """List, enum and input-object defaults used to raise NotImplementedError."""
    got = _defaults(
        "query Q("
        "$xs: [Int!] = [1, 2],"
        "$c: Color = RED,"
        "$f: Filter = {a: 1, b: [\"x\"], c: {d: null}}"
        ") { x }"
    )
    assert got["xs"] == [1, 2]
    assert got["c"] == "RED"
    assert got["f"] == {"a": 1, "b": ["x"], "c": {"d": None}}


def test_parse_value_node_boolean_literals():
    """``value_node.value`` is already a bool.

    The old ``value_node.value == "true"`` compared a bool to a str, so every
    literal ``true`` came out as ``False``.
    """
    got = _defaults("query Q($t: Boolean = true, $f: Boolean = false) { x }")
    assert got["t"] is True
    assert got["f"] is False


def test_complex_defaults_generate(complex_defaults_schema):
    """A document with list / enum / input-object variable defaults must generate."""
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/complex_defaults/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        complex_defaults_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    unit_test_with(
        generated_ast,
        "a = ComplexDefaults.Arguments(counts=[9])\n"
        "assert a.counts == [9]\n"
        # defaults are recorded as markers, not baked in, so they stay unset
        "assert 'color' not in a.model_dump(exclude_unset=True)\n",
    )
