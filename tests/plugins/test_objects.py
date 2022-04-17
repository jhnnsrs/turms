import pytest

from tests.plugins.utils import (
    build_schema_from_sdl,
    re_patterns_in_python_ast,
    python_from_ast,
    TestCase,
    GeneratedTestCaseFlavour,
    TestCaseGenerator,
)
from turms.errors import NoEnumFound

test_case_generator = TestCaseGenerator(GeneratedTestCaseFlavour.OBJECT_TYPE)


@pytest.mark.parametrize(
    ["test_case"],
    test_case_generator.make_test_cases_primitive_field_value()
    + test_case_generator.make_test_cases_nested_field_value()
    + test_case_generator.make_test_cases_description()
    + test_case_generator.make_test_cases_deprecation()
    + test_case_generator.make_test_cases_is_keyword()
)
def test_objects(test_case: TestCase, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_ast = objects_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)


@pytest.mark.parametrize(["test_case"], test_case_generator.make_test_cases_enum_field_value())
def test_objects_without_enum_plugin(test_case: TestCase, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    with pytest.raises(NoEnumFound):
        objects_plugin.generate_ast(schema, config, registry)


@pytest.mark.parametrize(["test_case"], test_case_generator.make_test_cases_enum_field_value())
def test_objects_without_enum_plugin(test_case: TestCase, enums_plugin, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    enum_ast = enums_plugin.generate_ast(schema, config, registry)
    objects_ast = objects_plugin.generate_ast(schema, config, registry)
    ast = enum_ast + objects_ast
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, ast), python_from_ast(ast)
