import ast
import re
from typing import List, Union

from graphql import GraphQLSchema, build_ast_schema, parse, DEFAULT_DEPRECATION_REASON
from pydantic import BaseModel


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


class TestCase(BaseModel):
    sdl: str
    expected_re_patterns: List[str]


def re_token_can_be_forward_reference(string: str) -> str:
    """Regular expression that matches <string> and '<string>'."""
    return fr"(?:\'{string}\'|{string})"


class TestCaseGenerator:
    gql_type_identifier: str = NotImplemented

    @staticmethod
    def _format_list_for_parametrize(test_cases: Union[TestCase, List[TestCase]]) -> List[List[TestCase]]:
        if not isinstance(test_cases, list):
            test_cases = [test_cases]
        return [[case] for case in test_cases]

    @classmethod
    def make_test_cases_primitive_field_value(cls):
        test_cases = [
            TestCase(
                sdl="""
                %s OptionalField {
                  test: String
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class OptionalField",
                    r"test: Optional\[str\]"
                ]
            ),
            TestCase(
                sdl="""
                %s MandatoryField {
                  test: String!
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class MandatoryField",
                    r"test: str"
                ]
            ),
            TestCase(
                sdl="""
                %s OptionalInsideOptionalList {
                  test: [String]
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class OptionalInsideOptionalList",
                    r"test: Optional\[List\[Optional\[str\]\]\]"
                ]
            ),
            TestCase(
                sdl="""
                %s MandatoryInsideOptionalList {
                  test: [String!]
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class MandatoryInsideOptionalList",
                    r"test: Optional\[List\[str\]\]"
                ]
            ),
            TestCase(
                sdl="""
                %s OptionalInsideMandatoryList {
                  test: [String]!
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class OptionalInsideMandatoryList",
                    r"test: List\[Optional\[str\]\]"
                ]
            ),
            TestCase(
                sdl="""
                %s MandatoryInsideMandatoryList {
                  test: [String!]!
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class MandatoryInsideMandatoryList",
                    r"test: List\[str\]"
                ]
            ),
        ]
        return cls._format_list_for_parametrize(test_cases)

    @classmethod
    def make_test_cases_enum_field_value(cls):
        test_cases = [
            TestCase(
                sdl="""
                enum Foo {
                  bar
                  baz
                }

                %s EnumField {
                  foo: Foo!
                }
                """ % cls.gql_type_identifier,
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

                %s OptionalEnumField {
                  foo: Foo
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class Foo\(str, Enum\):",
                    r"bar = \'bar\'",
                    r"baz = \'baz\'",
                    r"class OptionalEnumField",
                    fr"foo: Optional\[{re_token_can_be_forward_reference('Foo')}\]",
                ]
            )
        ]
        return cls._format_list_for_parametrize(test_cases)

    @classmethod
    def make_test_cases_nested_field_value(cls) -> List[List[TestCase]]:
        test_cases = [
            TestCase(
                sdl="""
                %s MandatoryNestedField {
                  foo: Bar!
                }
    
                %s Bar {
                  test: String!
                }
                """ % (cls.gql_type_identifier, cls.gql_type_identifier),
                expected_re_patterns=[
                    r"class MandatoryNestedField",
                    fr"foo: {re_token_can_be_forward_reference('Bar')}",
                    r"class Bar",
                    r"test: str"
                ]
            ),
            TestCase(
                sdl="""
                %s OptionalNestedField {
                  foo: Bar
                }
    
                %s Bar {
                  test: String!
                }
                """ % (cls.gql_type_identifier, cls.gql_type_identifier),
                expected_re_patterns=[
                    r"class OptionalNestedField",
                    fr"foo: Optional\[{re_token_can_be_forward_reference('Bar')}\]",
                    r"class Bar",
                    r"test: str"
                ]
            ),

            TestCase(
                sdl="""
                %s OptionalNestedTypeInListField {
                  foo: [Bar]!
                }
    
                %s Bar {
                  test: String!
                }
                """ % (cls.gql_type_identifier, cls.gql_type_identifier),
                expected_re_patterns=[
                    r"class OptionalNestedTypeInListField",
                    fr"foo: List\[Optional\[{re_token_can_be_forward_reference('Bar')}\]\]",
                    r"class Bar",
                    r"test: str"
                ]
            ),

            TestCase(
                sdl="""
                %s MandatoryNestedTypeInListField {
                  foo: [Bar!]!
                }
    
                %s Bar {
                  test: String!
                }
                """ % (cls.gql_type_identifier, cls.gql_type_identifier),
                expected_re_patterns=[
                    r"class MandatoryNestedTypeInListField",
                    fr"foo: List\[{re_token_can_be_forward_reference('Bar')}\]",
                    r"class Bar",
                    r"test: str"
                ]
            ),
        ]
        return cls._format_list_for_parametrize(test_cases)

    @classmethod
    def make_test_cases_description(cls):
        test_cases = [
            TestCase(
                sdl='''
            """
            Test description
            """
            %s TypeWithDescription {
              test: String!
            }
            ''' % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class TypeWithDescription",
                    r"\"Test description\"",
                    r"test: str"
                ]
            ),

            TestCase(
                sdl="""
            %s FieldWithDescription {
              "Test description"
              test: String!
            }
            """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class FieldWithDescription",
                    r"\'Test description\'",
                    r"test: str"
                ]
            ),
        ]
        return cls._format_list_for_parametrize(test_cases)

    @classmethod
    def make_test_cases_deprecation(cls):
        test_cases = [
            TestCase(
                sdl="""
                        %s DeprecatedFieldWithReason {
                          test: String! @deprecated(reason: "Custom deprecation reason")
                        }
                        """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class DeprecatedFieldWithReason",
                    r"test: str",
                    r"\'DEPRECATED: Custom deprecation reason\'"
                ]
            ),

            TestCase(
                sdl="""
                        %s DeprecatedFieldWithoutReason {
                          test: String! @deprecated
                        }
                        """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class DeprecatedFieldWithoutReason",
                    r"test: str",
                    fr"\'DEPRECATED: {DEFAULT_DEPRECATION_REASON}\'"
                ]
            ),
        ]
        return cls._format_list_for_parametrize(test_cases)

    @classmethod
    def make_test_cases_skip_underscore(cls, should_skip: bool):
        on_skip_patterns = ["^$"]  # empty string
        on_generated_patterns = [
            r"class _SkipUnderscore",
            r"test: Optional\[str\]",
        ]
        return cls._format_list_for_parametrize(
            TestCase(
                sdl="""
                %s _SkipUnderscore {
                  test: String
                }""" % cls.gql_type_identifier,
                expected_re_patterns=on_skip_patterns if should_skip else on_generated_patterns
            )
        )

    @classmethod
    def make_test_cases_skip_double_underscore(cls, should_skip: bool):
        on_skip_patterns = ["^$"]  # empty string
        on_generated_patterns = [
            r"class __SkipDoubleUnderscore",
            r"test: Optional\[str\]",
        ]
        return cls._format_list_for_parametrize(
            TestCase(
                sdl="""
                %s __SkipDoubleUnderscore {
                 test: String
                }""" % cls.gql_type_identifier,
                expected_re_patterns=on_skip_patterns if should_skip else on_generated_patterns
            )
        )

    @classmethod
    def make_test_cases_is_keyword(cls):
        return cls._format_list_for_parametrize(
            TestCase(
                sdl="""
                %s FieldIsKeyword {
                  from: Int!
                }
                """ % cls.gql_type_identifier,
                expected_re_patterns=[
                    r"class FieldIsKeyword",
                    r"from_: int = Field\(alias='from'\)"
                ]
            )
        )
