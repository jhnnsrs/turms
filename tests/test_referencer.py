from turms.referencer import create_reference_registry_from_documents
from turms.utils import parse_documents

from .utils import build_relative_glob


def test_referencer_arkitekt(arkitekt_schema):

    x = build_relative_glob("/documents/arkitekt/**/*.graphql")
    docs = parse_documents(arkitekt_schema, x)
    z = create_reference_registry_from_documents(arkitekt_schema, docs)
    assert "ArgPortInput" in z.inputs, "ArgPortInput should be referenced"


def test_referencer_countries(countries_schema):

    x = build_relative_glob("/documents/countries/*.graphql")
    docs = parse_documents(countries_schema, x)
    z = create_reference_registry_from_documents(countries_schema, docs)
    assert (
        "StringQueryOperatorInput" not in z.inputs
    ), "StringQueryOperatorInput should be skipped"


def test_referencer_enum_in_union_fragment(union_schema):

    x = build_relative_glob("/documents/unions/*.graphql")
    docs = parse_documents(union_schema, x)
    z = create_reference_registry_from_documents(union_schema, docs)
    assert "TestEnum1" in z.enums, "TestEnum1 should be referenced (in operation)"
    assert "TestEnum2" in z.enums, "TestEnum2 should be referenced (in fragment)"
