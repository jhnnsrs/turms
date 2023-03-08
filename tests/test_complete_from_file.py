from turms.run import generate


def test_create_multi_schema(multi_schema_projects):
    for key, project in multi_schema_projects.items():
        generate(project)


def test_create_countries_headers(test_countries_projects):
    for key, project in test_countries_projects.items():
        generate(project)


def test_create_skip_unreferenced(skip_unreferenced_project):
    for key, project in skip_unreferenced_project.items():
        generate(project)
