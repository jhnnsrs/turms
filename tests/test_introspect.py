import pytest
from turms.helpers import build_schema_from_introspect_url
from turms.errors import GenerationError


def test_introspect():
    build_schema_from_introspect_url("https://countries.trevorblades.com/")


def test_introspect_bearer():
    build_schema_from_introspect_url(
        "https://countries.trevorblades.com/", bearer_token="oisnoinsosin"
    )


def test_introspect_wrong():
    with pytest.raises(GenerationError):
        build_schema_from_introspect_url("https://countries.sddfdf.com/")
