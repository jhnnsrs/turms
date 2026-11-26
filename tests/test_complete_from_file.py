import pytest

from turms.config import GraphQLProject
from turms.run import generate


def test_create_multi_schema(multi_schema_projects: dict[str, GraphQLProject]) -> None:
    for _key, project in multi_schema_projects.items():
        generate(project)


@pytest.mark.network
def test_create_countries_headers(
    test_countries_projects: dict[str, GraphQLProject],
) -> None:
    for _key, project in test_countries_projects.items():
        generate(project)


@pytest.mark.network
def test_create_skip_unreferenced(
    skip_unreferenced_project: dict[str, GraphQLProject],
) -> None:
    for _key, project in skip_unreferenced_project.items():
        generate(project)
