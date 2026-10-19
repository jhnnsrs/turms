"""Tests for ``directive_class_vars``: directive applications stamped onto generated classes.

Mirrors arkitekt-service's ``@identified(by: "@mikro/arraydataset")``: a type carries the
structure it is known by, and every class turms generates for that type -- its fragment,
each nested selection of it, an inline fragment on it, an interface's implementation --
must carry it too, because a nested selection is a class of its own and not a subclass of
the fragment.
"""

import pytest
from graphql import build_client_schema, introspection_from_schema, parse
from pydantic import ValidationError

from turms.config import GeneratorConfig
from turms.errors import GenerationError, RegistryError
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import build_ast_schema, generate_ast
from turms.stylers.default import DefaultStyler

from .utils import unit_test_with

schema_sdl = """
directive @identified(by: String!) on OBJECT
directive @tag(name: String!) repeatable on OBJECT | INPUT_OBJECT
directive @marked on OBJECT | INTERFACE
directive @kind(of: Kind!) on OBJECT
directive @level(n: Int = 3) on OBJECT

enum Kind {
  ALPHA
  BETA
}

interface Lens @marked {
  id: ID!
  dataset: Dataset!
}

type ArrayLens implements Lens @identified(by: "@x/arraylens") {
  id: ID!
  dataset: Dataset!
  shape: [Int!]!
}

type TableLens implements Lens @identified(by: "@x/tablelens") @tag(name: "a") @tag(name: "b") {
  id: ID!
  dataset: Dataset!
  rows: Int!
}

type Dataset @identified(by: "@x/dataset") @kind(of: BETA) @level {
  id: ID!
  name: String!
}

type Plain {
  id: ID!
}

union Thing = Dataset | Plain

input MakeInput @tag(name: "in") {
  name: String!
}

type Query {
  dataset(id: ID!): Dataset!
  lens(id: ID!): Lens!
  thing: Thing!
  plain: Plain!
}

type Mutation {
  make(input: MakeInput!): Dataset!
}
"""

documents = """
fragment Dataset on Dataset {
  id
  name
}

fragment ArrayLens on ArrayLens {
  id
  shape
  dataset {
    id
  }
}

query GetDataset($id: ID!) {
  dataset(id: $id) {
    ...Dataset
  }
}

query GetLens($id: ID!) {
  lens(id: $id) {
    id
    dataset {
      id
      name
    }
    ... on TableLens {
      rows
    }
    ...ArrayLens
  }
}

query GetThing {
  thing {
    ... on Dataset {
      id
    }
    ... on Plain {
      id
    }
  }
}

query GetPlain {
  plain {
    id
  }
}

mutation Make($input: MakeInput!) {
  make(input: $input) {
    id
  }
}
"""

IDENTIFIED = {"directive": "identified", "argument": "by", "attribute": "__identifier__"}


def _generate(tmp_path, rules, sdl=schema_sdl, docs=documents, plugins=None, schema=None):
    (tmp_path / "ops.graphql").write_text(docs)
    config = GeneratorConfig(documents=str(tmp_path / "*.graphql"), directive_class_vars=rules)
    return generate_ast(
        config,
        schema if schema is not None else build_ast_schema(parse(sdl)),
        stylers=[DefaultStyler()],
        plugins=plugins
        if plugins is not None
        else [EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin()],
    )


def test_every_class_generated_for_a_type_carries_its_identifier(tmp_path):
    """The fragment, a nested selection, an inline fragment, an interface's implementations."""
    generated_ast = _generate(tmp_path, [IDENTIFIED])

    unit_test_with(
        generated_ast,
        """
        assert Dataset.__identifier__ == '@x/dataset'
        assert ArrayLens.__identifier__ == '@x/arraylens'
        # A nested selection is its own class, not a subclass of the fragment.
        assert not issubclass(ArrayLensDataset, Dataset)
        assert ArrayLensDataset.__identifier__ == '@x/dataset'
        assert GetLensLensDataset.__identifier__ == '@x/dataset'
        assert MakeMake.__identifier__ == '@x/dataset'
        assert GetThingDatasetInlineFragment.__identifier__ == '@x/dataset'
        # An interface's implementations each say their own type.
        assert GetLensLensBaseArrayLens.__identifier__ == '@x/arraylens'
        assert GetLensLensBaseTableLens.__identifier__ == '@x/tablelens'

        # A type without the directive gets no attribute.
        for cls in (GetThingPlainInlineFragment, GetPlainPlain, GetLensLensBase, GetLensLensBaseCatchAll):
            assert not hasattr(cls, '__identifier__'), cls

        # A class variable, never a field.
        assert '__identifier__' not in Dataset.model_fields
        assert Dataset.model_validate({'id': '1', 'name': 'a'}).__identifier__ == '@x/dataset'
        """,
    )


def test_a_repeatable_directive_an_enum_a_default_and_a_marker(tmp_path):
    """A tuple for a repeatable directive, an enum's name, a definition's default, ``True`` for presence."""
    generated_ast = _generate(
        tmp_path,
        [
            {"directive": "tag", "argument": "name", "attribute": "__tags__"},
            {"directive": "kind", "argument": "of", "attribute": "__kind__"},
            {"directive": "level", "argument": "n", "attribute": "__level__"},
            {"directive": "marked", "attribute": "__marked__"},
        ],
    )

    unit_test_with(
        generated_ast,
        """
        assert GetLensLensBaseTableLens.__tags__ == ('a', 'b')
        assert MakeInput.__tags__ == ('in',)
        assert Dataset.__kind__ == 'BETA'
        assert Dataset.__level__ == 3
        # On the interface's own class; its implementations inherit it.
        assert GetLensLensBase.__marked__ is True
        assert GetLensLensBaseArrayLens.__marked__ is True
        assert not hasattr(Dataset, '__marked__')
        assert '__tags__' not in MakeInput.model_fields
        MakeInput(name='x')
        """,
    )


def test_the_objects_plugin_stamps_its_classes_too(tmp_path):
    generated_ast = _generate(tmp_path, [IDENTIFIED], docs="query GetPlain { plain { id } }", plugins=[EnumsPlugin(), InputsPlugin(), ObjectsPlugin()])

    unit_test_with(
        generated_ast,
        """
        assert Dataset.__identifier__ == '@x/dataset'
        assert TableLens.__identifier__ == '@x/tablelens'
        assert not hasattr(Plain, '__identifier__')
        """,
    )


def test_a_directive_the_schema_does_not_declare_is_an_error(tmp_path):
    with pytest.raises(RegistryError, match="no directive @identifed"):
        _generate(tmp_path, [{**IDENTIFIED, "directive": "identifed"}])


def test_an_argument_the_directive_does_not_take_is_an_error(tmp_path):
    with pytest.raises(RegistryError, match="no argument 'name'"):
        _generate(tmp_path, [{**IDENTIFIED, "argument": "name"}])


def test_an_introspected_schema_cannot_show_applications_and_is_an_error(tmp_path):
    introspected = build_client_schema(introspection_from_schema(build_ast_schema(parse(schema_sdl))))
    with pytest.raises(RegistryError, match="introspected"):
        _generate(tmp_path, [IDENTIFIED], schema=introspected)


def test_a_stamp_named_like_a_field_is_an_error(tmp_path):
    """Pydantic would read the class variable as the field's default."""
    with pytest.raises(GenerationError, match="'name' is also a field"):
        _generate(tmp_path, [{**IDENTIFIED, "attribute": "name"}])


@pytest.mark.parametrize("attribute", ["not-a-name", "class"])
def test_an_attribute_that_is_no_python_identifier_is_refused_by_the_config(attribute):
    with pytest.raises(ValidationError, match="not a python identifier"):
        GeneratorConfig(documents="*.graphql", directive_class_vars=[{**IDENTIFIED, "attribute": attribute}])


def test_a_misspelled_rule_key_is_refused_by_the_config():
    with pytest.raises(ValidationError):
        GeneratorConfig(documents="*.graphql", directive_class_vars=[{**IDENTIFIED, "attribut": "__x__"}])


def test_a_type_generated_as_no_class_is_an_error(tmp_path):
    """A union, an enum or a scalar is never a class a stamp could land on."""
    sdl = schema_sdl.replace("union Thing = Dataset | Plain", 'union Thing @tag(name: "u") = Dataset | Plain').replace(
        "directive @tag(name: String!) repeatable on OBJECT | INPUT_OBJECT",
        "directive @tag(name: String!) repeatable on OBJECT | INPUT_OBJECT | UNION",
    )
    with pytest.raises(RegistryError, match="Thing carries @tag, but a GraphQLUnionType"):
        _generate(tmp_path, [{"directive": "tag", "argument": "name", "attribute": "__tags__"}], sdl=sdl)


def test_a_oneof_input_is_generated_as_a_union_and_is_an_error(tmp_path):
    sdl = schema_sdl + """
directive @oneOf on INPUT_OBJECT

input PickInput @oneOf @tag(name: "p") {
  byId: ID
  byName: String
}

extend type Query {
  pick(input: PickInput!): Dataset!
}
"""
    docs = documents + """
query Pick($input: PickInput!) {
  pick(input: $input) {
    id
  }
}
"""
    with pytest.raises(GenerationError, match="PickInput would carry __tags__, but a @oneOf input"):
        _generate(tmp_path, [{"directive": "tag", "argument": "name", "attribute": "__tags__"}], sdl=sdl, docs=docs)


def test_a_single_value_is_typed_as_its_literal(tmp_path):
    """What lets a `Protocol` with `ClassVar[Literal[...]]` tell a dataset's classes from a lens's."""
    import ast

    generated = ast.unparse(
        ast.fix_missing_locations(
            ast.Module(
                body=_generate(
                    tmp_path,
                    [
                        IDENTIFIED,
                        {"directive": "kind", "argument": "of", "attribute": "__kind__"},
                        {"directive": "level", "argument": "n", "attribute": "__level__"},
                        {"directive": "tag", "argument": "name", "attribute": "__tags__"},
                        {"directive": "marked", "attribute": "__marked__"},
                    ],
                ),
                type_ignores=[],
            )
        )
    )
    assert "__identifier__: ClassVar[Literal['@x/dataset']] = '@x/dataset'" in generated
    assert "__kind__: ClassVar[Literal['BETA']] = 'BETA'" in generated
    assert "__level__: ClassVar[Literal[3]] = 3" in generated
    assert "__marked__: ClassVar[Literal[True]] = True" in generated
    # A tuple keeps its element type.
    assert "__tags__: ClassVar[tuple[str, ...]] = ('a', 'b')" in generated
