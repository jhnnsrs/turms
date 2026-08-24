from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, unit_test_with


def _generate(hello_world_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/root_typename/*.graphql"),
    )
    return generate_ast(
        config,
        hello_world_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )


def test_root_typename_is_a_real_field(hello_world_schema):
    """A ``__typename`` selected at the operation root must survive as a field.

    Emitting it verbatim would give the class a ``__typename`` attribute, which
    python name-mangles to ``_RootTypename__typename``; pydantic then treats the
    leading underscore as a private attribute and drops it from ``model_fields``
    entirely, silently discarding the server's value.
    """
    generated_ast = _generate(hello_world_schema)

    unit_test_with(
        generated_ast,
        "assert 'typename' in RootTypename.model_fields,"
        " '__typename at the operation root was dropped'\n"
        "assert '__typename' not in str(RootTypename.model_fields)"
        " or RootTypename.model_fields['typename'].alias == '__typename'\n",
    )


def test_root_typename_round_trips(hello_world_schema):
    generated_ast = _generate(hello_world_schema)

    unit_test_with(
        generated_ast,
        "m = RootTypename.model_validate("
        "{'__typename': 'Query', 'hello': [{'__typename': 'World',"
        " 'message': 'hi'}]})\n"
        "assert m.typename == 'Query'\n"
        "assert m.hello[0].message == 'hi'\n",
    )
