import ast

import pytest
from turms.config import GeneratorConfig, Extensions, ConfigProxy
from turms.run import generate, GraphQLProject
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.stylers.default import DefaultStyler
from turms.parsers.polyfill import PolyfillParser
from turms.run import generate_ast, build_schema_from_schema_type
from .utils import build_relative_glob, unit_test_with, ExecuteError
import pydantic


def test_project_pipeline():
    config = GraphQLProject(
        schema="https://countries.trevorblades.com/",
        scalar_definitions={"_Any": "typing.Any"},
        extensions=Extensions(
            turms=GeneratorConfig(
                plugins=[
                    ConfigProxy(type="turms.plugins.enums.EnumsPlugin"),
                    ConfigProxy(type="turms.plugins.inputs.InputsPlugin"),
                    ConfigProxy(type="turms.plugins.objects.ObjectsPlugin"),
                ],
                stylers=[
                    ConfigProxy(type="turms.stylers.default.DefaultStyler"),
                ],
                parsers=[ConfigProxy(type="turms.parsers.polyfill.PolyfillParser")],
            )
        ),
    )

    generated_ast = generate(config)

    assert generated_ast
