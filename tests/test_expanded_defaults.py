"""An input expanded into a client method's parameters: a non-null field with a default may be left
out (the server applies the default), as the GraphQL spec says; one without a default may not."""

import ast
import inspect

from graphql import parse

from turms.config import GeneratorConfig
from turms.plugins.client import ClientPlugin, ClientPluginConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import build_ast_schema, generate_ast
from turms.stylers.default import DefaultStyler

SDL = """
input MakeInput {
  name: String!
  allowMesh: Boolean! = false
  note: String
}

type Thing {
  id: ID!
}

type Query {
  thing: Thing!
}

type Mutation {
  make(input: MakeInput!): Thing!
}
"""

DOCUMENTS = """
mutation Make($input: MakeInput!) {
  make(input: $input) {
    id
  }
}
"""


def _api(tmp_path):
    (tmp_path / "ops.graphql").write_text(DOCUMENTS)
    config = GeneratorConfig(documents=str(tmp_path / "*.graphql"))
    tree = generate_ast(
        config,
        build_ast_schema(parse(SDL)),
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            ClientPlugin(config=ClientPluginConfig(client_class="ThingApi", expand_input_types=["input"], async_methods=False)),
        ],
    )
    namespace: dict = {}
    exec(ast.unparse(ast.fix_missing_locations(ast.Module(body=tree, type_ignores=[]))), namespace)
    return namespace


def test_a_non_null_field_with_a_default_is_an_optional_parameter(tmp_path):
    namespace = _api(tmp_path)
    parameters = inspect.signature(namespace["ThingApi"].make).parameters
    assert parameters["name"].default is inspect.Parameter.empty
    assert parameters["allow_mesh"].default is not inspect.Parameter.empty
    assert parameters["note"].default is not inspect.Parameter.empty


def test_a_field_left_out_is_not_sent_and_the_server_applies_its_default(tmp_path):
    namespace = _api(tmp_path)
    sent = []

    class Client(namespace["ThingApi"]):
        def execute(self, operation, variables, **kwargs):
            sent.append(variables)
            return operation.model_validate({"make": {"__typename": "Thing", "id": "1"}})

    Client().make("x")
    Client().make("y", allow_mesh=True)
    assert sent[0]["input"] == {"name": "x"}
    assert sent[1]["input"] == {"name": "y", "allowMesh": True}
