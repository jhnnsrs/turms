import ast

import pytest
from .utils import build_relative_glob, unit_test_with, ExecuteError
from pydantic import ValidationError

from turms.config import GeneratorConfig, OptionsConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.default import DefaultStyler


@pytest.mark.network
def test_allow_population_by_field_name(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            allow_population_by_field_name=True,
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(
        generated_ast,
        "Countries(countries=[CountriesCountries(emoji_u='soinsisn',phone='sdf', capital='dfsdf')]).countries[0].emoji_u",
    )
    assert "from enum import Enum" in generated, "EnumPlugin not working"


@pytest.mark.network
def test_extra_forbid(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="forbid",
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    ast.unparse(ast.fix_missing_locations(md))
    with pytest.raises(ExecuteError):
        unit_test_with(
            generated_ast,
            "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf', hundi='soinsoin')]).countries[0].emoji_u",
        )


@pytest.mark.network
def test_extra_allow(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="allow",
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(
        generated_ast,
        "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf', hundi='soinsoin')]).countries[0].emoji_u",
    )


@pytest.mark.network
def test_from_attributes(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            from_attributes=True,
        ),
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(
        generated_ast,
        "Countries(countries=[CountriesCountries(emojiU='soinsisn', phone='sdf', capital='dfsdf')]).countries[0].emoji_u",
    )


@pytest.mark.parametrize(
    "removed_option, replacement",
    [("orm_mode", "from_attributes"), ("allow_mutation", "freeze")],
)
def test_pydantic_v1_options_are_rejected(removed_option, replacement):
    """The pydantic v1 option spellings name their replacement instead of
    failing as an anonymous 'extra inputs are not permitted'."""
    with pytest.raises(ValidationError, match=replacement):
        OptionsConfig(enabled=True, **{removed_option: True})


def test_pydantic_v1_target_is_rejected():
    """pydantic_version: v2 still loads but is dropped entirely; v1 is an error."""
    config = GeneratorConfig(pydantic_version="v2")
    assert not hasattr(config, "pydantic_version")
    with pytest.raises(ValidationError, match="pydantic v2"):
        GeneratorConfig(pydantic_version="v1")


def test_pydantic_version_does_not_survive_a_dump():
    """The dead key carries forward into neither the dump nor the json schema,
    so a dumped project.json does not resurrect it."""
    assert "pydantic_version" not in GeneratorConfig().model_dump()
    assert "pydantic_version" not in GeneratorConfig.model_json_schema()["properties"]


@pytest.mark.network
def test_generated_options_module_imports_without_warnings(countries_schema):
    """Every option the OptionsConfig can emit must be a config key pydantic v2
    actually accepts -- a v1 leftover surfaces as a UserWarning on import."""
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        options=OptionsConfig(
            enabled=True,
            extra="forbid",
            use_enum_values=True,
            validate_assignment=True,
            populate_by_name=True,
            from_attributes=True,
        ),
    )
    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )
    unit_test_with(generated_ast, "", strict_warnings=True)


# --------------------------------------------------------------------------- #
# turms 2.0 config cleanup
# --------------------------------------------------------------------------- #


def test_dumped_project_can_be_loaded_back():
    """`dump_configuration: true` has to emit the graphql-config `schema` key, not
    the python field name, or the file it writes is neither valid graphql-config
    nor loadable by turms itself."""
    import json

    from turms.config import Extensions, GraphQLProject

    project = GraphQLProject(
        schema="tests/schemas/beasts.graphql",
        extensions=Extensions(turms=GeneratorConfig()),
    )
    dumped = json.loads(project.model_dump_json(by_alias=True))
    assert "schema" in dumped and "schema_url" not in dumped
    assert GraphQLProject(**dumped).schema_url == project.schema_url


def test_option_sections_ignore_bare_environment_variables(monkeypatch):
    """OptionsConfig/FreezeConfig used to be BaseSettings without an env_prefix, so
    a stray `ENABLED` or `EXTRA` in the environment silently rewrote every
    generated model's config."""
    monkeypatch.setenv("ENABLED", "true")
    monkeypatch.setenv("EXTRA", "forbid")
    monkeypatch.setenv("PROJECTS", "nonsense")

    config = GeneratorConfig()
    assert config.options.enabled is False
    assert config.options.extra is None
    assert config.freeze.enabled is False


@pytest.mark.parametrize(
    "spelling", ["populate_by_name", "allow_population_by_field_name"]
)
def test_populate_by_name_accepts_both_spellings(spelling):
    """The v1 spelling stays a deprecated alias so existing configs keep loading."""
    assert OptionsConfig(**{spelling: True}).populate_by_name is True


def test_operations_plugin_accepts_both_populate_by_name_spellings():
    from turms.plugins.operations import OperationsPluginConfig

    for spelling in (
        "arguments_populate_by_name",
        "arguments_allow_population_by_field_name",
    ):
        config = OperationsPluginConfig(**{spelling: True})
        assert config.arguments_populate_by_name is True


def test_operations_plugin_env_override_still_works(monkeypatch):
    """A validation_alias on a BaseSettings field would silently replace the
    prefixed env lookup rather than add to it, so the alias lives in a
    before-validator instead."""
    from turms.plugins.operations import OperationsPluginConfig

    monkeypatch.setenv("TURMS_PLUGINS_OPERATIONS_ARGUMENTS_POPULATE_BY_NAME", "true")
    assert OperationsPluginConfig().arguments_populate_by_name is True


def test_inputs_plugin_names_the_replacement_for_the_removed_option():
    from turms.plugins.inputs import InputsPluginConfig

    with pytest.raises(ValidationError, match="options.populate_by_name"):
        InputsPluginConfig(allow_population_by_field_name=True)


def test_removed_polyfill_parser_names_itself():
    """A config still listing the parser must say it was removed rather than
    failing as an opaque 'Invalid import'."""
    from turms.config import ConfigProxy

    with pytest.raises(ValidationError, match="removed in turms 2.0"):
        GeneratorConfig(
            parsers=[ConfigProxy(type="turms.parsers.polyfill.PolyfillParser")]
        )


@pytest.mark.parametrize("version", ["3.7", "3.8"])
def test_eol_python_targets_are_rejected(version):
    with pytest.raises(ValidationError):
        GeneratorConfig(min_python_version=version)
