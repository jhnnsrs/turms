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
