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
        documents=build_relative_glob("/documents/skip_include/*.graphql"),
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


def test_skip_and_include_make_fields_optional(hello_world_schema):
    """@skip / @include let the server omit the field, so it cannot be required.

    ``message`` is ``String!`` in the schema, but a conditionally-included
    selection of it must still validate when the server leaves the key out.
    """
    generated_ast = _generate(hello_world_schema)

    unit_test_with(
        generated_ast,
        # the server omitted both conditional fields
        "m = ConditionalHello.model_validate({'always': 'hi'})\n"
        "assert m.skipped is None\n"
        "assert m.included is None\n"
        "assert m.always == 'hi'\n"
        # and still accepts them when present
        "m2 = ConditionalHello.model_validate("
        "{'skipped': 'a', 'included': 'b', 'always': 'c'})\n"
        "assert (m2.skipped, m2.included, m2.always) == ('a', 'b', 'c')\n",
    )


def test_literal_false_skip_stays_required(hello_world_schema):
    """@skip(if: false) can never exclude the field, so it must stay required."""
    generated_ast = _generate(hello_world_schema)

    unit_test_with(
        generated_ast,
        "import pydantic\n"
        "assert LiteralAlwaysPresentHello.model_fields['message'].is_required()\n"
        "try:\n"
        "    LiteralAlwaysPresentHello.model_validate({})\n"
        "except pydantic.ValidationError:\n"
        "    pass\n"
        "else:\n"
        "    raise AssertionError('message should still be required')\n",
    )


def test_directive_on_union_inline_fragment(union_schema):
    """Union selections build their inline-fragment classes on a separate path.

    ``forward`` is ``String!`` inside a conditional inline fragment, so it must
    be Optional; ``nana`` is ``Int!`` inside an unconditional one and must stay
    required.
    """
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/skip_include_union/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        union_schema,
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
        "assert not CondUnionFooInlineFragment.model_fields['forward'].is_required()\n"
        "assert CondUnionBarInlineFragment.model_fields['nana'].is_required()\n",
    )
