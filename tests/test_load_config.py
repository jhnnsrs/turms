import pytest
from .utils import build_relative_glob
from turms.run import gen, scan_folder_for_configs

from turms.errors import GenerationError
from turms.run import load_projects_from_configpath


@pytest.fixture()
def parsable_configs():
    return scan_folder_for_configs(build_relative_glob("/configs/parsable"))


@pytest.fixture()
def unparsable_configs():
    return scan_folder_for_configs(build_relative_glob("/configs/unparsable"))


@pytest.fixture()
def parsable_configs_single():
    return scan_folder_for_configs(build_relative_glob("/configs/parsable_single"))


def test_load_projects(parsable_configs):
    assert parsable_configs, "No parsable configs found"
    for config in parsable_configs:
        projects = load_projects_from_configpath(config)
        assert len(projects) > 1, "Should have at least one project"


def test_load_projects(parsable_configs_single):
    assert parsable_configs_single, "No parsable configs found"
    for config in parsable_configs_single:
        projects = load_projects_from_configpath(config)
        assert len(projects) == 1, "Should have at exactly one project"


def test_load_unparsable(unparsable_configs):
    assert unparsable_configs, "No unparsable configs found"
    for config in unparsable_configs:
        with pytest.raises(GenerationError):
            load_projects_from_configpath(config)
