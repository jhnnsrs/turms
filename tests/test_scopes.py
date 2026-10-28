"""The scopes plugin: the scopes a client needs, from ``@auth(required_scopes: ...)`` on the root
fields its operations select."""

import ast

import pytest
from graphql import build_client_schema, introspection_from_schema, parse

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.scopes import ScopesPlugin, ScopesPluginConfig
from turms.run import build_ast_schema, generate_ast
from turms.stylers.default import DefaultStyler

schema_sdl = """
directive @auth(required_scopes: [String!], any_role_of: [String!]) on FIELD_DEFINITION

type Image {
  id: ID!
}

type Query {
  image(id: ID!): Image! @auth(required_scopes: ["mikro_read"])
  images: [Image!]! @auth(required_scopes: ["mikro_read"])
  secret: Image! @auth(required_scopes: ["mikro_admin_only"])
  open: Image!
}

type Mutation {
  createImage: Image! @auth(required_scopes: ["mikro_write"], any_role_of: ["mikro_editor"])
  annotate: Image! @auth(required_scopes: ["mikro_annotate"])
}

type Subscription {
  images: Image! @auth(required_scopes: ["mikro_watch"])
}
"""

documents = """
fragment Roots on Query {
  images {
    id
  }
}

query Get($id: ID!) {
  image(id: $id) {
    id
  }
  ...Roots
  open {
    id
  }
}

mutation Create {
  ... on Mutation {
    createImage {
      id
    }
  }
}

subscription Watch {
  images {
    id
  }
}
"""


def _scopes(tmp_path, schema=None, plugin_config=None):
    (tmp_path / "ops.graphql").write_text(documents)
    config = GeneratorConfig(documents=str(tmp_path / "*.graphql"))
    tree = generate_ast(
        config,
        schema if schema is not None else build_ast_schema(parse(schema_sdl)),
        stylers=[DefaultStyler()],
        plugins=[ScopesPlugin(config=plugin_config or ScopesPluginConfig())],
    )
    module = ast.unparse(ast.Module(body=tree, type_ignores=[]))
    namespace: dict = {}
    exec(module, namespace)
    return namespace


def test_the_scopes_of_the_root_fields_used_are_gathered(tmp_path):
    assert _scopes(tmp_path)["SCOPES"] == ["mikro_read", "mikro_watch", "mikro_write"]


def test_fields_no_operation_selects_are_left_out(tmp_path):
    scopes = _scopes(tmp_path)["SCOPES"]
    assert "mikro_admin_only" not in scopes and "mikro_annotate" not in scopes


def test_the_list_can_be_named(tmp_path):
    assert "NEEDED" in _scopes(tmp_path, plugin_config=ScopesPluginConfig(attribute="NEEDED"))


def test_an_introspected_schema_is_refused(tmp_path):
    introspected = build_client_schema(introspection_from_schema(build_ast_schema(parse(schema_sdl))))
    with pytest.raises(GenerationError, match="introspected"):
        _scopes(tmp_path, schema=introspected)


def test_a_schema_without_the_directive_is_refused(tmp_path):
    with pytest.raises(GenerationError, match="declares no directive @auth"):
        _scopes(tmp_path, schema=build_ast_schema(parse("type Query { image: Int }")))


def test_an_argument_the_directive_lacks_is_refused(tmp_path):
    with pytest.raises(GenerationError, match="no argument any_scope_of"):
        _scopes(tmp_path, plugin_config=ScopesPluginConfig(arguments=["any_scope_of"]))
