import pytest

from tests.plugins.utils import (
    build_schema_from_sdl,
    re_patterns_in_python_ast,
    python_from_ast,
    TestCase,
    TestCaseGenerator,
)
from turms.errors import NoEnumFound


class ObjectTypeTestCaseGenerator(TestCaseGenerator):
    gql_type_identifier = "type"


class InterfaceTypeTestCaseGenerator(TestCaseGenerator):
    gql_type_identifier = "interface"


@pytest.mark.parametrize(
    ["test_case"],
    ObjectTypeTestCaseGenerator.make_test_cases_primitive_field_value()
    + ObjectTypeTestCaseGenerator.make_test_cases_nested_field_value()
    + ObjectTypeTestCaseGenerator.make_test_cases_description()
    + ObjectTypeTestCaseGenerator.make_test_cases_deprecation()
    + ObjectTypeTestCaseGenerator.make_test_cases_is_keyword()
)
def test_objects(test_case: TestCase, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_ast = objects_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)


@pytest.mark.parametrize(
    ["test_case"],
    InterfaceTypeTestCaseGenerator.make_test_cases_primitive_field_value()
    + InterfaceTypeTestCaseGenerator.make_test_cases_nested_field_value()
    + InterfaceTypeTestCaseGenerator.make_test_cases_description()
    + InterfaceTypeTestCaseGenerator.make_test_cases_deprecation()
    + InterfaceTypeTestCaseGenerator.make_test_cases_is_keyword()
)
def test_interfaces__implementation_not_required(test_case: TestCase, objects_plugin, config, registry):
    config.always_resolve_interfaces = False
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_ast = objects_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)


@pytest.mark.parametrize(["test_case"], ObjectTypeTestCaseGenerator.make_test_cases_enum_field_value())
def test_objects_without_enum_plugin(test_case: TestCase, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    with pytest.raises(NoEnumFound):
        objects_plugin.generate_ast(schema, config, registry)


@pytest.mark.parametrize(["test_case"], ObjectTypeTestCaseGenerator.make_test_cases_enum_field_value())
def test_objects_without_enum_plugin(test_case: TestCase, enums_plugin, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    enum_ast = enums_plugin.generate_ast(schema, config, registry)
    objects_ast = objects_plugin.generate_ast(schema, config, registry)
    ast = enum_ast + objects_ast
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, ast), python_from_ast(ast)
