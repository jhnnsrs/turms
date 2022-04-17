import pytest

from tests.plugins.utils import (
    build_schema_from_sdl,
    re_patterns_in_python_ast,
    python_from_ast,
    TestCase,
    re_token_can_be_forward_reference,
    TestCaseGenerator,
)
from turms.errors import NoEnumFound


def make_enum_test_cases_for_parametrize():
    test_cases = [
        TestCase(
            sdl="""
            enum Foo {
              bar
              baz
            }
    
            input EnumField {
              foo: Foo!
            }
            """,
            expected_re_patterns=[
                r"class Foo\(str, Enum\):",
                r"bar = \'bar\'",
                r"baz = \'baz\'",
                r"class EnumField",
                fr"foo: {re_token_can_be_forward_reference('Foo')}",
            ]
        ),

        TestCase(
            sdl="""
            enum Foo {
              bar
              baz
            }
        
            input OptionalEnumField {
              foo: Foo
            }
            """,
            expected_re_patterns=[
                r"class Foo\(str, Enum\):",
                r"bar = \'bar\'",
                r"baz = \'baz\'",
                r"class OptionalEnumField",
                fr"foo: Optional\[{re_token_can_be_forward_reference('Foo')}\]",
            ]
        )
    ]
    return [[case] for case in test_cases]


test_case_generator = TestCaseGenerator("input")


@pytest.mark.parametrize(
    ["test_case"],
    test_case_generator.make_test_cases_primitive_field_types()
    + test_case_generator.make_test_cases_nested_field_types()
    + test_case_generator.make_test_cases_description()
    + test_case_generator.make_test_cases_deprecation()
    + test_case_generator.make_test_cases_skip_underscore(skip=True)
    + test_case_generator.make_test_cases_skip_double_underscore(skip=True),
)
def test_input(test_case: TestCase, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)


@pytest.mark.parametrize(["test_case"], make_enum_test_cases_for_parametrize())
def test_input_enum_without_enum_plugin(test_case, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    with pytest.raises(NoEnumFound):
        inputs_plugin.generate_ast(schema, config, registry)


@pytest.mark.parametrize(["test_case"], make_enum_test_cases_for_parametrize())
def test_input_enum_with_enum_plugin(test_case, enums_plugin, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    enums_ast = enums_plugin.generate_ast(schema, config, registry)
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(
        test_case.expected_re_patterns,
        enums_ast + inputs_ast
    ), python_from_ast(enums_ast + inputs_ast)


@pytest.fixture
def is_key_word_test_case():
    return TestCase(
        sdl="""
        input FieldIsKeyword {
          from: Int!
        }
        """,
        expected_re_patterns=[
            r"class FieldIsKeyword",
            r"from_: int = Field\(alias='from'\)"
        ]
    )


def test_keyword(is_key_word_test_case, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(is_key_word_test_case.sdl)
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(
        is_key_word_test_case.expected_re_patterns, inputs_ast
    ), python_from_ast(inputs_ast)
