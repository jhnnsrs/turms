import pytest

from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.registry import ClassRegistry
from turms.stylers.default import DefaultStyler


@pytest.fixture
def enums_plugin():
    return EnumsPlugin()


@pytest.fixture
def inputs_plugin():
    return InputsPlugin()


@pytest.fixture
def objects_plugin():
    return ObjectsPlugin()


@pytest.fixture
def config():
    return GeneratorConfig()


@pytest.fixture
def registry(config):
    return ClassRegistry(config, stylers=[DefaultStyler()])
