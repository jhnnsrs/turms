import pytest
from turms.errors import GenerationError
from turms.helpers import load_introspection_from_url
from graphql import build_client_schema


def test_introspect():
    return build_client_schema(
        load_introspection_from_url("https://countries.trevorblades.com/")
    )


def test_introspect_wrong():
    with pytest.raises(GenerationError):
        return build_client_schema(
            load_introspection_from_url("https://countries.sddfdf.com/")
        )
