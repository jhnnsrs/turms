import pytest
from turms.run import (
    build_schema_from_schema_type,
    scan_folder_for_configs,
    load_projects_from_configpath,
)
from .utils import build_relative_glob
from pydantic import AnyHttpUrl
from turms.helpers import load_introspection_from_url, build_client_schema


@pytest.fixture(scope="session")
def builtin_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/builtin.graphql")
    )


@pytest.fixture(scope="session")
def hello_world_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/helloworld.graphql")
    )


@pytest.fixture(scope="session")
def beast_schema():
    return build_schema_from_schema_type(build_relative_glob("/schemas/beasts.graphql"))


@pytest.fixture(scope="session")
def arkitekt_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/arkitekt.graphql")
    )


@pytest.fixture(scope="session")
def countries_schema():
    return build_client_schema(
        load_introspection_from_url("https://countries.trevorblades.com/")
    )


@pytest.fixture(scope="session")
def keyword_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/keyword.graphql")
    )


@pytest.fixture(scope="session")
def nested_input_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/nested_inputs.graphql")
    )


@pytest.fixture(scope="session")
def union_schema():
    return build_schema_from_schema_type(build_relative_glob("/schemas/union.graphql"))


@pytest.fixture(scope="session")
def schema_directive_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/directive.graphql")
    )


@pytest.fixture(scope="session")
def scalar_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/scalars.graphql")
    )


@pytest.fixture(scope="session")
def unimplemented_interface_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/interface_without_implementating_types.graphql")
    )


@pytest.fixture(scope="session")
def multiple_inheritance_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/multiple_inhertiance.graphql")
    )


@pytest.fixture(scope="session")
def multiple_forward_references_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/multiple_forward_references.graphql")
    )


@pytest.fixture(scope="session")
def multi_interface_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/multi_interface.graphql")
    )


@pytest.fixture(scope="session")
def mro_test_schema():
    return build_schema_from_schema_type(build_relative_glob("/schemas/mro.graphql"))


@pytest.fixture(scope="session")
def forward_reference_to_interface_schema():
    return build_schema_from_schema_type(
        build_relative_glob("/schemas/forward_reference_to_interface.graphql")
    )


@pytest.fixture(scope="session")
def parsable_configs():
    return scan_folder_for_configs(build_relative_glob("/configs/parsable"))


@pytest.fixture(scope="session")
def unparsable_configs():
    return scan_folder_for_configs(build_relative_glob("/configs/unparsable"))


@pytest.fixture(scope="session")
def parsable_configs_single():
    return scan_folder_for_configs(build_relative_glob("/configs/parsable_single"))


@pytest.fixture(scope="session")
def multi_schema_field_config():
    return scan_folder_for_configs(build_relative_glob("/configs/multi_schema"))


@pytest.fixture(scope="session")
def multi_schema_projects():
    configs = scan_folder_for_configs(build_relative_glob("/configs/multi_schema"))
    return load_projects_from_configpath(configs[0])


@pytest.fixture(scope="session")
def test_countries_projects():
    return load_projects_from_configpath(
        build_relative_glob("/configs/test_countries.yaml")
    )
