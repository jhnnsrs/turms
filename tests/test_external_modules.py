"""One project generates the enums and inputs, another generates over them.

``external_modules`` is what lets a package ship its wire vocabulary in one
module and its fragments, operations and client in a second that *imports* the
first, rather than regenerating 96 pydantic models into both.
"""

import pytest

from turms.config import GeneratorConfig
from turms.errors import GenerationError, RegistryError
from turms.plugins.enums import EnumsPlugin, EnumsPluginConfig
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin, InputsPluginConfig
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast, parse_asts_to_string
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, unit_test_with_external

STYLERS = [CapitalizeStyler(), SnakeCaseStyler()]
EXTERNAL = "external_schema"
SCALARS = {"QString": "str", "Any": "typing.Any", "Callback": "str", "UUID": "pydantic.UUID4"}
DOCUMENTS = "/documents/arkitekt/**/*.graphql"


def _protocol_ast(schema):
    """Project A: every enum and input in the schema, and nothing else."""
    config = GeneratorConfig(
        documents=build_relative_glob(DOCUMENTS), scalar_definitions=SCALARS
    )
    return generate_ast(
        config,
        schema,
        stylers=STYLERS,
        plugins=[
            EnumsPlugin(config=EnumsPluginConfig(skip_unreferenced=False)),
            InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False)),
        ],
    )


def _api_config(**kwargs):
    return GeneratorConfig(
        documents=build_relative_glob(DOCUMENTS),
        scalar_definitions=SCALARS,
        external_modules=[{"module": EXTERNAL, "kinds": ["enum", "input"], **kwargs}],
    )


def _api_ast(schema, config=None, plugins=None):
    """Project B: fragments and operations, over A's enums and inputs."""
    config = config or _api_config()
    return generate_ast(
        config,
        schema,
        stylers=STYLERS,
        plugins=plugins if plugins is not None else [FragmentsPlugin(), OperationsPlugin()],
    )


# --------------------------------------------------------------------------- #
# References resolve, as imports
# --------------------------------------------------------------------------- #


def test_an_external_input_is_imported_not_generated(arkitekt_schema):
    """Operation ``Arguments`` resolve with ``allow_forward=False``, so before this
    feature the same generation raised "could not find corresponding type"."""
    generated = parse_asts_to_string(_api_ast(arkitekt_schema))

    assert f"from {EXTERNAL} import" in generated
    assert "DefinitionInput" in generated
    assert "class DefinitionInput(BaseModel)" not in generated


def test_an_external_enum_is_a_name_not_a_string_annotation(arkitekt_schema):
    """A fragment's enum field used to become a forward reference whose
    ``model_rebuild()`` then failed at import time."""
    generated = parse_asts_to_string(_api_ast(arkitekt_schema))

    assert "class NodeType(str, Enum)" not in generated
    assert "'NodeType'" not in generated


def test_the_pair_actually_imports_and_runs(arkitekt_schema):
    """The real proof: both modules on disk, the second importing the first."""
    unit_test_with_external(
        _protocol_ast(arkitekt_schema),
        _api_ast(arkitekt_schema),
        "",
        module_name=EXTERNAL,
    )


# --------------------------------------------------------------------------- #
# Only what is used
# --------------------------------------------------------------------------- #


def test_an_unreferenced_external_type_is_not_imported(arkitekt_schema):
    """Seeding is exhaustive, importing is not: the import is registered where a
    type is referenced. Otherwise all 96 names land in the import block and ruff
    flags every one of them."""
    generated = parse_asts_to_string(_api_ast(arkitekt_schema))

    imported = {
        name.strip()
        for line in generated.splitlines()
        if line.startswith(f"from {EXTERNAL} import ")
        for name in line.split("import", 1)[1].split(",")
    }
    all_enums_and_inputs = {
        key
        for key in arkitekt_schema.type_map
        if not key.startswith("__")
        and type(arkitekt_schema.type_map[key]).__name__
        in ("GraphQLEnumType", "GraphQLInputObjectType")
    }

    assert imported
    assert imported < all_enums_and_inputs, (
        "every seeded type was imported; the import registration is not lazy"
    )


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


def test_generating_a_type_that_is_also_external_is_refused(arkitekt_schema):
    """Running the inputs plugin *and* declaring its types external is a
    configuration mistake, and it is the plugin that gives way."""
    generated = parse_asts_to_string(
        _api_ast(
            arkitekt_schema,
            plugins=[
                InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False)),
                FragmentsPlugin(),
                OperationsPlugin(),
            ],
        )
    )

    assert "class DefinitionInput(BaseModel)" not in generated
    assert f"from {EXTERNAL} import" in generated


def test_two_external_modules_claiming_one_type_are_refused(arkitekt_schema):
    config = GeneratorConfig(
        documents=build_relative_glob(DOCUMENTS),
        scalar_definitions=SCALARS,
        external_modules=[
            {"module": "a", "kinds": ["enum"]},
            {"module": "b", "kinds": ["enum"]},
        ],
    )

    # Seeding happens before the plugin loop, so this is not wrapped in the
    # plugin's "X failed!" GenerationError -- it names the real problem.
    with pytest.raises(RegistryError, match="can only come from one external module"):
        generate_ast(
            config, arkitekt_schema, stylers=STYLERS, plugins=[FragmentsPlugin()]
        )


def test_a_name_override_is_what_gets_imported(arkitekt_schema):
    """The escape hatch, for when the other project exported a different name."""
    generated = parse_asts_to_string(
        _api_ast(arkitekt_schema, config=_api_config(names={"NodeType": "RenamedKind"}))
    )

    assert "RenamedKind" in generated


# --------------------------------------------------------------------------- #
# The config surface
# --------------------------------------------------------------------------- #


def test_a_config_declaring_a_split_loads():
    from turms.run import load_projects_from_configpath

    projects = load_projects_from_configpath(
        build_relative_glob("/configs/test_external_split.yaml")
    )

    external = projects["beasts"].extensions.turms.external_modules
    assert [e.module for e in external] == ["examples.protocol.schema"]
    assert external[0].from_project == "beasts_protocol"


def test_projects_with_different_stylers_are_refused():
    """Class names are derived from the typename and the stylers, so two projects
    only agree on them while their stylers agree. Caught at load, not at import."""
    from turms.run import load_projects_from_configpath

    with pytest.raises(GenerationError, match="different stylers"):
        load_projects_from_configpath(
            build_relative_glob("/configs/test_external_styler_mismatch.yaml")
        )
