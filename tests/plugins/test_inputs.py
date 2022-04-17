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

test_case_generator = TestCaseGenerator(GeneratedTestCaseFlavour.INPUT_OBJECT_TYPE)


@pytest.mark.parametrize(
    ["test_case"],
    test_case_generator.make_test_cases_primitive_field_value()
    + test_case_generator.make_test_cases_nested_field_value()
    + test_case_generator.make_test_cases_description()
    + test_case_generator.make_test_cases_deprecation()
    + test_case_generator.make_test_cases_is_keyword()
)
def test_input(test_case: TestCase, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)


@pytest.mark.parametrize(["test_case"], test_case_generator.make_test_cases_enum_field_value())
def test_input_enum_without_enum_plugin(test_case, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    with pytest.raises(NoEnumFound):
        inputs_plugin.generate_ast(schema, config, registry)


@pytest.mark.parametrize(["test_case"], test_case_generator.make_test_cases_enum_field_value())
def test_input_enum_with_enum_plugin(test_case, enums_plugin, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    enums_ast = enums_plugin.generate_ast(schema, config, registry)
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(
        test_case.expected_re_patterns,
        enums_ast + inputs_ast
    ), python_from_ast(enums_ast + inputs_ast)


@pytest.mark.parametrize(["test_case"],
                         test_case_generator.make_test_cases_skip_underscore(should_skip=True)
                         + test_case_generator.make_test_cases_skip_double_underscore(should_skip=True))
def test_skip_underscore(test_case: TestCase, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_plugin.config.skip_underscore = True
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)


@pytest.mark.parametrize(["test_case"],
                         test_case_generator.make_test_cases_skip_underscore(should_skip=False)
                         + test_case_generator.make_test_cases_skip_double_underscore(should_skip=False))
def test_ignore_underscore(test_case: TestCase, inputs_plugin, config, registry):
    schema = build_schema_from_sdl(test_case.sdl)
    inputs_plugin.config.skip_underscore = False
    inputs_ast = inputs_plugin.generate_ast(schema, config, registry)
    assert re_patterns_in_python_ast(test_case.expected_re_patterns, inputs_ast), python_from_ast(inputs_ast)
