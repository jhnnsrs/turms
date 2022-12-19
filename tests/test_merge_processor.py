import ast
import json

import pytest
from .utils import build_relative_glob
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.processors.merge import MergeProcessor, merge_code, MergeProcessorConfig
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler
from turms.helpers import build_schema_from_glob
from turms.parsers.polyfill import PolyfillParser, PolyfillPluginConfig


def test_merge_code():
    """Tests the merge_code function"""

    with open(build_relative_glob("/merge_pairs/old.py"), "r") as f:
        old_code = f.read()

    with open(build_relative_glob("/merge_pairs/new.py"), "r") as f:
        new_code = f.read()

    result = merge_code(old_code, new_code, MergeProcessorConfig())

    with open(build_relative_glob("/merge_pairs/updated.py"), "r") as f:
        new_code = f.read()
    assert (
        result == new_code
    ), "The merge_code function did not merge the code correctly"
