import pytest

from tests.plugins.utils import (
    build_schema_from_sdl,
    re_patterns_in_python_ast,
    python_from_ast,
    TestCase,
    TestCaseGenerator,
)

test_case_generator = TestCaseGenerator("type")


@pytest.mark.parametrize(
    ["test_case"],
    test_case_generator.make_test_cases_primitive_field_types()
    + test_case_generator.make_test_cases_nested_field_types()
    + test_case_generator.make_test_cases_description()
    + test_case_generator.make_test_cases_deprecation()
    + test_case_generator.make_test_cases_skip_underscore(skip=False)
    + test_case_generator.make_test_cases_skip_double_underscore(skip=True),
)
def test_objects(test_case: TestCase, objects_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_ast = objects_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)
