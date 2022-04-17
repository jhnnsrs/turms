import ast
import re
from typing import List

import pytest
from graphql import build_ast_schema, parse, GraphQLSchema
from graphql.type.directives import DEFAULT_DEPRECATION_REASON
from pydantic import BaseModel

from turms.config import GeneratorConfig
from turms.errors import NoEnumFound
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.registry import ClassRegistry
from turms.stylers.default import DefaultStyler


def build_schema_from_sdl(sdl: str) -> GraphQLSchema:
    return build_ast_schema(parse(sdl))


def re_patterns_in_python_ast(patterns: List[str], python_ast: List[ast.AST]) -> bool:
    python_string = python_from_ast(python_ast)
    return re_patterns_in_string(patterns, python_string)


def python_from_ast(code_ast: List[ast.AST]) -> str:
    module = ast.Module(body=code_ast, type_ignores=[])
    module_with_added_lineno_and_col_offset = ast.fix_missing_locations(module)
    parsed_code = ast.unparse(module_with_added_lineno_and_col_offset)
    return parsed_code


def re_patterns_in_string(substrings: List[str], string: str) -> bool:
    return all(
        bool(re.search(substring, string, re.MULTILINE))
        for substring in substrings
    )


@pytest.fixture
def inputs_plugin():
    return InputsPlugin()


@pytest.fixture
def config():
    return GeneratorConfig()


@pytest.fixture
def registry(config):
    return ClassRegistry(config, stylers=[DefaultStyler()])


class TestCase(BaseModel):
    sdl: str
    expected_re_patterns: List[str]


def re_token_maybe_as_forward_reference(string: str) -> str:
    return fr"(?:\'{string}\'|{string})"


def make_test_cases_for_parametrize() -> List[List[TestCase]]:
    test_cases = [
        TestCase(
            sdl="""
            input OptionalField {
              test: String
            }
            """,
            expected_re_patterns=[
                r"class OptionalField",
                r"test: Optional\[str\]"
            ]
        ),

        TestCase(
            sdl="""
            input MandatoryField {
              test: String!
            }
            """,
            expected_re_patterns=[
                r"class MandatoryField",
                r"test: str"
            ]
        ),

        TestCase(
            sdl="""
            input OptionalInsideOptionalList {
              test: [String]
            }
            """,
            expected_re_patterns=[
                r"class OptionalInsideOptionalList",
                r"test: Optional\[List\[Optional\[str\]\]\]"
            ]
        ),
        TestCase(
            sdl="""
            input MandatoryInsideOptionalList {
              test: [String!]
            }
            """,
            expected_re_patterns=[
                r"class MandatoryInsideOptionalList",
                r"test: Optional\[List\[str\]\]"
            ]
        ),
        TestCase(
            sdl="""
            input OptionalInsideMandatoryList {
              test: [String]!
            }
            """,
            expected_re_patterns=[
                r"class OptionalInsideMandatoryList",
                r"test: List\[Optional\[str\]\]"
            ]
        ),

        TestCase(
            sdl="""
            input MandatoryInsideMandatoryList {
              test: [String!]!
            }
            """,
            expected_re_patterns=[
                r"class MandatoryInsideMandatoryList",
                r"test: List\[str\]"
            ]
        ),

        TestCase(
            sdl="""
            input MandatoryInputField {
              foo: Bar!
            }
            
            input Bar {
              test: String!
            }
            """,
            expected_re_patterns=[
                r"class MandatoryInputField",
                fr"foo: {re_token_maybe_as_forward_reference('Bar')}",
                r"class Bar",
                r"test: str"
            ]
        ),
        TestCase(
            sdl="""
            input OptionalInputField {
              foo: Bar
            }
            
            input Bar {
              test: String!
            }
            """,
            expected_re_patterns=[
                r"class OptionalInputField",
                fr"foo: Optional\[{re_token_maybe_as_forward_reference('Bar')}\]",
                r"class Bar",
                r"test: str"
            ]
        ),

        TestCase(
            sdl="""
            input OptionalInputInListField {
              foo: [Bar]!
            }
            
            input Bar {
              test: String!
            }
            """,
            expected_re_patterns=[
                r"class OptionalInputInListField",
                fr"foo: List\[Optional\[{re_token_maybe_as_forward_reference('Bar')}\]\]",
                r"class Bar",
                r"test: str"
            ]
        ),

        TestCase(
            sdl="""
            input MandatoryInputInListField {
              foo: [Bar!]!
            }
            
            input Bar {
              test: String!
            }
            """,
            expected_re_patterns=[
                r"class MandatoryInputInListField",
                fr"foo: List\[{re_token_maybe_as_forward_reference('Bar')}\]",
                r"class Bar",
                r"test: str"
            ]
        ),

        TestCase(
            sdl='''
            """
            Test description
            """
            input InputWithDescription {
              test: String!
            }
            ''',
            expected_re_patterns=[
                r"class InputWithDescription",
                r"\"Test description\"",
                r"test: str"
            ]
        ),

        TestCase(
            sdl="""
            input FieldWithDescription {
              "Test description"
              test: String!
            }
            """,
            expected_re_patterns=[
                r"class FieldWithDescription",
                r"\'Test description\'",
                r"test: str"
            ]
        ),

        TestCase(
            sdl="""
            input DeprecatedFieldWithReason {
              test: String! @deprecated(reason: "Custom deprecation reason")
            }
            """,
            expected_re_patterns=[
                r"class DeprecatedFieldWithReason",
                r"test: str",
                r"\'DEPRECATED: Custom deprecation reason\'"
            ]
        ),

        TestCase(
            sdl="""
            input DeprecatedFieldWithoutReason {
              test: String! @deprecated
            }
            """,
            expected_re_patterns=[
                r"class DeprecatedFieldWithoutReason",
                r"test: str",
                fr"\'DEPRECATED: {DEFAULT_DEPRECATION_REASON}\'"
            ]
        ),
        TestCase(
            sdl="""
            input _SkipType {
              test: String
            }""",
            expected_re_patterns=[
                "^$"  # empty string
            ]
        )
    ]
    return [[case] for case in test_cases]


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
                fr"foo: {re_token_maybe_as_forward_reference('Foo')}",
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
                fr"foo: Optional\[{re_token_maybe_as_forward_reference('Foo')}\]",
            ]
        )
    ]
    return [[case] for case in test_cases]


@pytest.mark.parametrize(["test_case"], make_test_cases_for_parametrize())
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
def test_input_enum_with_enum_plugin(test_case, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    enums_plugin = EnumsPlugin()
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
