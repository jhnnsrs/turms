import ast
import re
from typing import List

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
    return fr"(?:\'{string}\'|{string})"


class TestCaseGenerator:
    def __init__(self, gql_type_identifier: str):
        assert gql_type_identifier in ["type", "input"]
        self.gql_type_identifier = gql_type_identifier

    @staticmethod
    def _format_list_for_parametrize(test_cases: List[TestCase]) -> List[List[TestCase]]:
        return [[case] for case in test_cases]

    def make_test_cases_primitive_field_types(self):
        test_cases = [
            TestCase(
                sdl="""
                %s OptionalField {
                  test: String
                }
                """ % self.gql_type_identifier,
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
                """ % self.gql_type_identifier,
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
                """ % self.gql_type_identifier,
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
                """ % self.gql_type_identifier,
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
                """ % self.gql_type_identifier,
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
                """ % self.gql_type_identifier,
                expected_re_patterns=[
                    r"class MandatoryInsideMandatoryList",
                    r"test: List\[str\]"
                ]
            ),
        ]
        return self._format_list_for_parametrize(test_cases)

    def make_test_cases_nested_field_types(self) -> List[List[TestCase]]:
        test_cases = [
            TestCase(
                sdl="""
                %s MandatoryNestedField {
                  foo: Bar!
                }
    
                %s Bar {
                  test: String!
                }
                """ % (self.gql_type_identifier, self.gql_type_identifier),
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
                """ % (self.gql_type_identifier, self.gql_type_identifier),
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
                """ % (self.gql_type_identifier, self.gql_type_identifier),
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
                """ % (self.gql_type_identifier, self.gql_type_identifier),
                expected_re_patterns=[
                    r"class MandatoryNestedTypeInListField",
                    fr"foo: List\[{re_token_can_be_forward_reference('Bar')}\]",
                    r"class Bar",
                    r"test: str"
                ]
            ),
        ]
        return self._format_list_for_parametrize(test_cases)

    def make_test_cases_description(self):
        test_cases = [
            TestCase(
                sdl='''
            """
            Test description
            """
            %s TypeWithDescription {
              test: String!
            }
            ''' % self.gql_type_identifier,
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
            """ % self.gql_type_identifier,
                expected_re_patterns=[
                    r"class FieldWithDescription",
                    r"\'Test description\'",
                    r"test: str"
                ]
            ),
        ]
        return self._format_list_for_parametrize(test_cases)

    def make_test_cases_deprecation(self):
        test_cases = [
            TestCase(
                sdl="""
                        %s DeprecatedFieldWithReason {
                          test: String! @deprecated(reason: "Custom deprecation reason")
                        }
                        """ % self.gql_type_identifier,
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
                        """ % self.gql_type_identifier,
                expected_re_patterns=[
                    r"class DeprecatedFieldWithoutReason",
                    r"test: str",
                    fr"\'DEPRECATED: {DEFAULT_DEPRECATION_REASON}\'"
                ]
            ),
        ]
        return self._format_list_for_parametrize(test_cases)

    def make_test_cases_skip_underscore(self, skip: bool):
        on_skip_patterns = ["^$"]  # empty string
        on_generated_patterns = [
            r"class _SkipUnderscore",
            r"test: Optional\[str\]",
        ]
        test_cases = [
            TestCase(
                sdl="""
                       %s _SkipUnderscore {
                         test: String
                       }""" % self.gql_type_identifier,
                expected_re_patterns=on_skip_patterns if skip else on_generated_patterns
            ),
        ]
        return self._format_list_for_parametrize(test_cases)

    def make_test_cases_skip_double_underscore(self, skip: bool):
        on_skip_patterns = ["^$"]  # empty string
        on_generated_patterns = [
            r"class __SkipDoubleUnderscore",
            r"test: Optional\[str\]",
        ]
        test_cases = [
            TestCase(
                sdl="""
                       %s __SkipDoubleUnderscore {
                         test: String
                       }""" % self.gql_type_identifier,
                expected_re_patterns=on_skip_patterns if skip else on_generated_patterns
            ),
        ]
        return self._format_list_for_parametrize(test_cases)
