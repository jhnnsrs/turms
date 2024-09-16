import pydantic
import pytest

from turms.config import GeneratorConfig
from .utils import build_relative_glob
from turms.run import scan_folder_for_single_config

from turms.errors import GenerationError
from turms.run import load_projects_from_configpath


def test_load_projects(parsable_configs):
    assert parsable_configs, "No parsable configs found"
    for config in parsable_configs:
        projects = load_projects_from_configpath(config)
        assert len(projects) >= 1, "Should have at least one project"


def test_load_projects_single(parsable_configs_single):
    assert parsable_configs_single, "No parsable configs found"
    for config in parsable_configs_single:
        projects = load_projects_from_configpath(config)
        assert len(projects) == 1, "Should have at exactly one project"


def test_load_unparsable(unparsable_configs):
    assert unparsable_configs, "No unparsable configs found"
    for config in unparsable_configs:
        with pytest.raises(GenerationError):
            load_projects_from_configpath(config)


def test_load_single_config():
    with pytest.raises(GenerationError):
        scan_folder_for_single_config(build_relative_glob("/configs/parsable"))
    with pytest.raises(GenerationError):
        scan_folder_for_single_config(build_relative_glob("/configs/empty"))


def test_failure_on_wrong_scalars():
    with pytest.raises(pydantic.ValidationError):
        GeneratorConfig(scalar_definitions={"X": "zzzzz"})
    with pytest.raises(pydantic.ValidationError):
        GeneratorConfig(scalar_definitions={"X": 15})


def test_load_multi_schemea_fields(multi_schema_field_config):
    assert multi_schema_field_config, "No parsable configs found"
    for config in multi_schema_field_config:
        projects = load_projects_from_configpath(config)
        print(projects)
        assert len(projects) == 1, "Should have at exactly one project"
