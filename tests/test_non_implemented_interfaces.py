import ast

import pytest
from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.helpers import build_schema_from_glob
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from tests.utils import (
    build_relative_glob,
    unit_test_with,
)


@pytest.fixture()
def unimplemented_interface_schema():
    return build_schema_from_glob(
        build_relative_glob("/schemas/interface_without_implementating_types.graphql")
    )


def test_generation_ok(unimplemented_interface_schema):
    config = GeneratorConfig(always_resolve_interfaces=False)

    generated_ast = generate_ast(
        config,
        unimplemented_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "Foo(forward=Ref(id=3))")


def test_generation_raises(unimplemented_interface_schema):
    config = GeneratorConfig(always_resolve_interfaces=True)

    with pytest.raises(GenerationError):
        generated_ast = generate_ast(
            config,
            unimplemented_interface_schema,
            stylers=[DefaultStyler()],
            plugins=[
                ObjectsPlugin(),
            ],
        )
