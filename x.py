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


def test_custom_scalar_generation():

    scalar_schema = build_schema_from_glob(
        build_relative_glob("/schemas/beasts.graphql")
    )
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        scalar_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    with open("l.py", "w") as f:
        f.write(parse_to_code(generated_ast))


test_custom_scalar_generation()
