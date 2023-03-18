import pytest
from turms.errors import GenerationError
from turms.helpers import load_introspection_from_url
from turms.run import build_schema_from_schema_type, SchemaType
from graphql import build_client_schema
from .utils import build_relative_glob
from pydantic import BaseModel


class Schema(BaseModel):
    schema_url: SchemaType


def test_introspect():
    return build_client_schema(
        load_introspection_from_url("https://countries.trevorblades.com/")
    )


def test_introspect_wrong():
    with pytest.raises(GenerationError):
        return build_client_schema(
            load_introspection_from_url("https://countries.sddfdf.com/")
        )


def test_do_not_allow_schema_introspection():

    s = Schema(schema_url="https://countries.trevorblades.com/")

    with pytest.raises(GenerationError):
        return build_schema_from_schema_type(s.schema_url, allow_introspection=False)


def test_with_schema_intrsopection():

    s = Schema(schema_url="https://countries.trevorblades.com/")

    build_schema_from_schema_type(s.schema_url, allow_introspection=True)


def test_build_multiple_files():
    t = build_relative_glob("/schemas/multi_schema/*.graphql")

    s = Schema(schema_url=t)

    build_schema_from_schema_type(s.schema_url, allow_introspection=True)


def test_build_multiple_files():
    t = [
        build_relative_glob("/schemas/multi_schema/beast_duo.graphql"),
        build_relative_glob("/schemas/multi_schema/beast_uno.graphql"),
    ]

    s = Schema(schema_url=t)

    build_schema_from_schema_type(s.schema_url, allow_introspection=True)


def test_build_multiple_files_error():
    t = [
        build_relative_glob("/schemas/multi_schema/beast_duo.graphql"),
        build_relative_glob(
            "/schemas/multi_schema/beast_unos.graphql"
        ),  # wrong file name
    ]

    s = Schema(schema_url=t)

    with pytest.raises(GenerationError):
        build_schema_from_schema_type(s.schema_url, allow_introspection=True)
