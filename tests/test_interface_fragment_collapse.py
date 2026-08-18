"""Regression tests for spreading an interface fragment into a field whose
type is a concrete implementation of that interface.

Previously turms collapsed ``createLayer { ...Layer }`` (where ``createLayer``
returns the concrete ``ImageLayer`` and ``Layer`` is a fragment on the
``Layer`` interface) to a bare ``Layer`` annotation. No class named ``Layer``
is emitted for an interface fragment, so the generated module raised
``NameError: name 'Layer' is not defined`` on import.
"""

import ast

from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, unit_test_with


def _generate(schema, with_funcs=True):
    plugins = [
        EnumsPlugin(),
        InputsPlugin(),
        FragmentsPlugin(),
        OperationsPlugin(),
    ]
    if with_funcs:
        plugins.append(
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
                        FunctionDefinition(
                            type="query", use="mocks.query", is_async=False
                        ),
                        FunctionDefinition(
                            type="mutation", use="mocks.query", is_async=False
                        ),
                    ]
                ),
            )
        )

    config = GeneratorConfig(
        documents=build_relative_glob(
            "/documents/interface_fragment_collapse/*/**.graphql"
        ),
    )
    return generate_ast(
        config,
        schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=plugins,
    )


def _class_field_annotation(tree, class_name, field_name):
    for node in tree:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id == field_name
                ):
                    return ast.unparse(stmt.annotation)
    raise AssertionError(f"{class_name}.{field_name} not found in generated tree")


def _func_return_annotation(tree, func_name):
    for node in tree:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            assert node.returns is not None
            return ast.unparse(node.returns)
    raise AssertionError(f"function {func_name} not found in generated tree")


def test_interface_fragment_collapse_imports(interface_fragment_collapse_schema):
    """The generated module must be valid, importable Python (no dangling
    reference to the interface fragment name)."""
    generated_ast = _generate(interface_fragment_collapse_schema)
    unit_test_with(generated_ast, "")


def test_interface_fragment_collapses_to_implementation(
    interface_fragment_collapse_schema,
):
    """Spreading the ``Layer`` interface fragment into the concrete
    ``ImageLayer`` field resolves to the implementation class."""
    generated_ast = _generate(interface_fragment_collapse_schema)

    # Operation class field
    assert (
        _class_field_annotation(generated_ast, "CreateLayer", "create_layer")
        == "LayerImageLayer"
    )
    # Collapsed convenience function return type
    assert _func_return_annotation(generated_ast, "create_layer") == "LayerImageLayer"


def test_interface_fragment_with_extra_field_inherits_implementation(
    interface_fragment_collapse_schema,
):
    """Selecting an extra field alongside the interface fragment must inherit
    from the implementation class (additional-bases path)."""
    generated_ast = _generate(interface_fragment_collapse_schema, with_funcs=False)

    for node in generated_ast:
        if (
            isinstance(node, ast.ClassDef)
            and node.name == "CreateLayerWithStatusCreatelayer"
        ):
            base_names = {b.id for b in node.bases if isinstance(b, ast.Name)}
            assert "LayerImageLayer" in base_names
            break
    else:
        raise AssertionError("CreateLayerWithStatusCreatelayer not generated")


def test_interface_field_still_produces_union(interface_fragment_collapse_schema):
    """A field that genuinely returns the interface must still generate the
    discriminated union (unchanged behaviour)."""
    generated_ast = _generate(interface_fragment_collapse_schema, with_funcs=False)
    annotation = _class_field_annotation(generated_ast, "GetLayer", "layer")
    assert "|" in annotation
    assert "discriminator" in annotation
