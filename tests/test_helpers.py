import os
import pytest
from .utils import DIR_NAME

from turms.helpers import import_string
from turms.run import build_schema_from_schema_type


def test_faulty_import():
    with pytest.raises(ImportError):
        import_string("invalid")

    with pytest.raises(ImportError):
        import_string("turms.plugins.base.RandomClass")


def test_schema_from_introspection_json():
    """
    Tests that the result of an introspection query can be read from a file.
    """
    build_schema_from_schema_type(
        os.path.join(DIR_NAME, "introspection/spacex.json"), allow_introspection=True
    )


def test_utf8_bom():
    """
    Tests that the files with UTF8-BOM are readable.
    """
    build_schema_from_schema_type(
        os.path.join(DIR_NAME, "schemas/helloworld_bom.graphql")
    )
