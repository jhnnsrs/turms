import os
import json
import pytest
from .utils import DIR_NAME

from turms.helpers import import_string, generate_headers
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


def test_generate_headers_no_env():
    results = generate_headers({"A-Header": "is here"}, {"Content-Type": "application/json"})

    assert results == {
        "A-Header": "is here",
        "Content-Type": "application/json",
    }

    results = generate_headers({}, None)
    assert results == {}


def test_generate_headers_with_env(monkeypatch):
    monkeypatch.setenv(
        "TURMS_HTTP_HEADERS",
        json.dumps(
            {
                "Authorization": "Bearer 1234",
            },
        ),
    )

    results = generate_headers({"A-Header": "is here"}, {"Content-Type": "application/json"})

    assert results == {
        "A-Header": "is here",
        "Content-Type": "application/json",
        "Authorization": "Bearer 1234"
    }
