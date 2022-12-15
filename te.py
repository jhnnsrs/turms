import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url
from tests.utils import build_relative_glob, unit_test_with, ExecuteError
import pydantic

countries_schema = build_schema_from_glob(
    build_relative_glob("/schemas/beasts.graphql")
)

config = GeneratorConfig(
    scalar_definitions={
        "QString": "str",
        "Any": "str",
        "UUID": "pydantic.UUID4",
        "ID": "strawberry.ID",
    }
)

generated_ast = generate_ast(
    config,
    countries_schema,
    stylers=[DefaultStyler()],
    plugins=[
        EnumsPlugin(),
        InputsPlugin(),
        StrawberryPlugin(),
    ],
    skip_forwards=True,
)


md = ast.Module(body=generated_ast, type_ignores=[])

# We need to unparse before otherwise there might be complaints with missing lineno
parsed_code = ast.unparse(ast.fix_missing_locations(md))
with open("beasts.py", "w") as f:
    f.write(parsed_code)
