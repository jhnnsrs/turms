import ast

import pytest

from .utils import (
    build_relative_glob,
    unit_test_with,
)
from turms.config import GeneratorConfig
from turms.run import generate_ast, build_schema_from_schema_type
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler


def test_generation(multiple_forward_references_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        multiple_forward_references_schema,
        stylers=[DefaultStyler()],
        plugins=[
            ObjectsPlugin(),
        ],
    )

    forward_refs = []
    for node in generated_ast:
        if not isinstance(node, ast.Expr):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Attribute):
            continue
        if node.value.func.attr == "update_forward_refs" and isinstance(
            node.value.func.value, ast.Name
        ):
            forward_refs.append(node.value.func.value.id)

    assert forward_refs == sorted(forward_refs)

    unit_test_with(generated_ast, "")
