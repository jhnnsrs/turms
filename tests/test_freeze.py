import ast

import pytest
from .utils import build_relative_glob, unit_test_with
from turms.config import GeneratorConfig
from turms.plugins.funcs import (
    FunctionDefinition,
    FuncsPlugin,
    FuncsPluginConfig,
)
from turms.run import generate_ast
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.stylers.default import DefaultStyler
from turms.run import generate_ast, build_schema_from_schema_type


def test_freeze_classes(countries_schema):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/countries/**.graphql"),
        freeze={
            "enabled": True,
        },
    )

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))
    unit_test_with(generated_ast, "x = Countries(countries=[])")
    assert "from enum import Enum" in generated, "EnumPlugin not working"
