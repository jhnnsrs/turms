

from .utils import (
    unit_test_with,
)
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler


def test_generation(forward_reference_to_interface_schema):
    config = GeneratorConfig(
        pydantic_version="v1",

    )

    generated_ast = generate_ast(

        config,
        forward_reference_to_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[
            ObjectsPlugin(),
        ],
    )

    unit_test_with(generated_ast, "")
