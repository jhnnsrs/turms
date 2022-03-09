import ast

import pytest
from turms.config import GeneratorConfig
from turms.run import gen, generate_ast
from turms.compat.funcs import unparse
from graphql.language import parse
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operation import OperationsPlugin
from turms.stylers.snake import SnakeNodeName
from turms.stylers.capitalize import Capitalizer


@pytest.fixture()
def hello_world_schema():
    with open("tests/schemas/helloworld.graphql") as f:
        schema = parse(f.read())
    return schema
