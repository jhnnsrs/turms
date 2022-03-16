import pytest
from graphql.language import parse


@pytest.fixture()
def hello_world_schema():
    with open("tests/schemas/helloworld.graphql") as f:
        schema = parse(f.read())
    return schema
