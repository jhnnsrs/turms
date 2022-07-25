import pytest

from turms.helpers import import_string, build_schema_from_glob


def test_faulty_import():
    with pytest.raises(ImportError):
        import_string("invalid")

    with pytest.raises(ImportError):
        import_string("turms.plugins.base.RandomClass")


def test_schema_from_introspection_json():
    """
    Tests that the result of an introspection query can be read from a file.
    """
    build_schema_from_glob("tests/introspection/spacex.json")


def test_utf8_bom():
    """
    Tests that the files with UTF8-BOM are readable.
    """
    build_schema_from_glob("tests/schemas/helloworld_bom.graphql")
