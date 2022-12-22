import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.stylers.default import DefaultStyler
from turms.helpers import build_schema_from_glob, build_schema_from_introspect_url
from tests.utils import build_relative_glob, unit_test_with, ExecuteError, parse_to_code
import pydantic

schema_directive_schema = build_schema_from_glob(
    build_relative_glob("/schemas/arkitekt.graphql")
)

countries_schema = build_schema_from_introspect_url(
    "https://countries.trevorblades.com/"
)


config = GeneratorConfig(
    scalar_definitions={
        "QString": "str",
        "Any": "str",
        "_Any": "typing.Any",
        "UUID": "pydantic.UUID4",
        "Callback": "str",
    }
)

generated_ast = generate_ast(
    config,
    countries_schema,
    stylers=[DefaultStyler()],
    plugins=[
        StrawberryPlugin(),
    ],
    skip_forwards=True,
)

code = parse_to_code(generated_ast)

with open("l.py", "w") as f:
    f.write(code)
