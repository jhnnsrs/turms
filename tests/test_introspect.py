import pytest
from graphql import build_client_schema
from pydantic import BaseModel

from turms.errors import GenerationError
from turms.helpers import load_introspection_from_url
from turms.run import SchemaType, build_schema_from_schema_type

from .utils import build_relative_glob


class Schema(BaseModel):
    schema_url: SchemaType


@pytest.mark.network
def test_introspect() -> None:
    build_client_schema(
        load_introspection_from_url("https://countries.trevorblades.com/")
    )


@pytest.mark.network
def test_introspect_wrong() -> None:
    with pytest.raises(GenerationError):
        build_client_schema(
            load_introspection_from_url("https://countries.sddfdf.com/")
        )


@pytest.mark.network
def test_do_not_allow_schema_introspection() -> None:
    s = Schema(schema_url="https://countries.trevorblades.com/")

    with pytest.raises(GenerationError):
        build_schema_from_schema_type(s.schema_url, allow_introspection=False)


@pytest.mark.network
def test_with_schema_intrsopection() -> None:
    s = Schema(schema_url="https://countries.trevorblades.com/")

    build_schema_from_schema_type(s.schema_url, allow_introspection=True)


def test_build_multiple_files_from_a_glob() -> None:
    t = build_relative_glob("/schemas/multi_schema/*.graphql")

    s = Schema(schema_url=t)

    build_schema_from_schema_type(s.schema_url, allow_introspection=True)


def test_build_multiple_files() -> None:
    t = [
        build_relative_glob("/schemas/multi_schema/beast_duo.graphql"),
        build_relative_glob("/schemas/multi_schema/beast_uno.graphql"),
    ]

    s = Schema(schema_url=t)

    build_schema_from_schema_type(s.schema_url, allow_introspection=True)


def test_build_multiple_files_error() -> None:
    t = [
        build_relative_glob("/schemas/multi_schema/beast_duo.graphql"),
        build_relative_glob(
            "/schemas/multi_schema/beast_unos.graphql"
        ),  # wrong file name
    ]

    s = Schema(schema_url=t)

    with pytest.raises(GenerationError):
        build_schema_from_schema_type(s.schema_url, allow_introspection=True)
