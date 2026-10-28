"""Tests for ``class_fields`` and ``client_fields``: class variables collected onto generated classes.

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

IDENTIFIED = {"name": "__identifier__", "collector": {"type": "type_directive", "directive": "identified", "argument": "by"}}



def _with(field, **collector):
    """``field`` with some of its collector's keys replaced."""
    return {**field, "collector": {**field["collector"], **collector}}


def _generate(tmp_path, rules, sdl=schema_sdl, docs=documents, plugins=None, schema=None):
    (tmp_path / "ops.graphql").write_text(docs)
    config = GeneratorConfig(documents=str(tmp_path / "*.graphql"), class_fields=rules)
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
            {"name": "__tags__", "collector": {"type": "type_directive", "directive": "tag", "argument": "name"}},
            {"name": "__kind__", "collector": {"type": "type_directive", "directive": "kind", "argument": "of"}},
            {"name": "__level__", "collector": {"type": "type_directive", "directive": "level", "argument": "n"}},
            {"name": "__marked__", "collector": {"type": "type_directive", "directive": "marked"}},
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
        _generate(tmp_path, [_with(IDENTIFIED, directive="identifed")])


def test_an_argument_the_directive_does_not_take_is_an_error(tmp_path):
    with pytest.raises(RegistryError, match="no argument 'name'"):
        _generate(tmp_path, [_with(IDENTIFIED, argument="name")])


def test_an_introspected_schema_cannot_show_applications_and_is_an_error(tmp_path):
    introspected = build_client_schema(introspection_from_schema(build_ast_schema(parse(schema_sdl))))
    with pytest.raises(RegistryError, match="introspected"):
        _generate(tmp_path, [IDENTIFIED], schema=introspected)


def test_a_stamp_named_like_a_field_is_an_error(tmp_path):
    """Pydantic would read the class variable as the field's default."""
    with pytest.raises(GenerationError, match="'name' is also a field"):
        _generate(tmp_path, [{**IDENTIFIED, "name": "name"}])


@pytest.mark.parametrize("attribute", ["not-a-name", "class"])
def test_a_name_that_is_no_python_identifier_is_refused_by_the_config(attribute):
    with pytest.raises(ValidationError, match="not a python identifier"):
        GeneratorConfig(documents="*.graphql", class_fields=[{**IDENTIFIED, "name": attribute}])


def test_a_misspelled_key_is_refused_by_the_config():
    with pytest.raises(ValidationError):
        GeneratorConfig(documents="*.graphql", class_fields=[{**IDENTIFIED, "nam": "__x__"}])


def test_a_type_generated_as_no_class_is_an_error(tmp_path):
    """A union, an enum or a scalar is never a class a stamp could land on."""
    sdl = schema_sdl.replace("union Thing = Dataset | Plain", 'union Thing @tag(name: "u") = Dataset | Plain').replace(
        "directive @tag(name: String!) repeatable on OBJECT | INPUT_OBJECT",
        "directive @tag(name: String!) repeatable on OBJECT | INPUT_OBJECT | UNION",
    )
    with pytest.raises(RegistryError, match="Thing would carry __tags__, but a GraphQLUnionType"):
        _generate(tmp_path, [{"name": "__tags__", "collector": {"type": "type_directive", "directive": "tag", "argument": "name"}}], sdl=sdl)


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
        _generate(tmp_path, [{"name": "__tags__", "collector": {"type": "type_directive", "directive": "tag", "argument": "name"}}], sdl=sdl, docs=docs)


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
                        {"name": "__kind__", "collector": {"type": "type_directive", "directive": "kind", "argument": "of"}},
                        {"name": "__level__", "collector": {"type": "type_directive", "directive": "level", "argument": "n"}},
                        {"name": "__tags__", "collector": {"type": "type_directive", "directive": "tag", "argument": "name"}},
                        {"name": "__marked__", "collector": {"type": "type_directive", "directive": "marked"}},
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


# --- client_fields: what a client's operations gather onto its class ----------------------

from turms.class_fields import Collector  # noqa: E402
from turms.plugins.client import ClientPlugin, ClientPluginConfig  # noqa: E402

client_sdl = """
directive @auth(required_scopes: [String!], any_role_of: [String!]) on FIELD_DEFINITION
directive @needs(scopes: [String!]!) on QUERY | MUTATION | SUBSCRIPTION

type Image {
  id: ID!
}

type Query {
  image(id: ID!): Image! @auth(required_scopes: ["read"])
  images: [Image!]! @auth(required_scopes: "read")
  secret: Image! @auth(required_scopes: ["admin_only"])
  open: Image!
}

extend type Query {
  thumbnails: [Image!]! @auth(required_scopes: ["read", "thumbnail"])
}

type Mutation {
  createImage: Image! @auth(required_scopes: ["write"], any_role_of: ["editor"])
}

type Subscription {
  images: Image! @auth(required_scopes: ["watch"])
}
"""

client_documents = """
query Get($id: ID!) @needs(scopes: ["extra"]) {
  image(id: $id) {
    id
  }
  images {
    id
  }
}

query Thumbs {
  thumbnails {
    id
  }
}

mutation Create {
  createImage {
    id
  }
}

subscription Watch {
  images {
    id
  }
}
"""

SCOPES = {
    "name": "__scopes__",
    "kind": "tuple[str, ...]",
    "collector": {"type": "root_field_directive", "directive": "auth", "argument": "required_scopes"},
    "combine": "union",
}


def _client(tmp_path, fields, docs=client_documents, sdl=client_sdl, schema=None):
    (tmp_path / "ops.graphql").write_text(docs)
    config = GeneratorConfig(documents=str(tmp_path / "*.graphql"))
    tree = generate_ast(
        config,
        schema if schema is not None else build_ast_schema(parse(sdl)),
        stylers=[DefaultStyler()],
        plugins=[EnumsPlugin(), InputsPlugin(), FragmentsPlugin(), OperationsPlugin(), ClientPlugin(config=ClientPluginConfig(client_class="ImageApi", client_fields=fields))],
    )
    import ast

    module = ast.unparse(ast.fix_missing_locations(ast.Module(body=tree, type_ignores=[])))
    namespace: dict = {}
    exec(module, namespace)
    return namespace["ImageApi"], module


def test_root_fields_are_found_through_fragments_spread_or_inlined_on_the_root_type():
    from turms.schema_lookup import root_field_nodes

    document = parse(
        "fragment Roots on Query { images { id } ...Deeper } fragment Deeper on Query { open { id } } "
        "query Q { image(id: 1) { id } ...Roots ... on Query { secret { id } } }"
    )
    fragments = {d.name.value: d for d in document.definitions if d.kind == "fragment_definition"}
    operation = next(d for d in document.definitions if d.kind == "operation_definition")
    assert [f.name.value for f in root_field_nodes(operation.selection_set, fragments)] == ["image", "images", "open", "secret"]


def test_the_root_fields_operations_select_are_gathered_onto_the_client_class(tmp_path):
    """Every operation's root fields, a subscription's and an extension's included, a single string a value."""
    api, module = _client(tmp_path, [SCOPES])
    assert api.__scopes__ == ("read", "thumbnail", "watch", "write")
    assert "__scopes__: ClassVar[tuple[str, ...]] = ('read', 'thumbnail', 'watch', 'write')" in module
    # What no operation selects is not asked for.
    assert "admin_only" not in api.__scopes__


def test_a_selected_root_field_that_says_nothing_fails_generation(tmp_path):
    docs = client_documents + "\nquery Open { open { id } }\n"
    with pytest.raises(GenerationError, match=r"Query.open \(operation Open\) gives no @auth\(required_scopes"):
        _client(tmp_path, [SCOPES], docs=docs)
    loose = _with(SCOPES, required=False)
    api, _ = _client(tmp_path, [loose], docs=docs)
    assert api.__scopes__ == ("read", "thumbnail", "watch", "write")


@pytest.mark.parametrize(
    ("combine", "kind", "expected"),
    [
        ("union", "tuple[str, ...]", ("read", "thumbnail", "watch", "write")),
        ("intersection", "tuple[str, ...]", ()),
        ("ordered", "list[str]", ["read", "thumbnail", "write", "watch"]),
        ("all", "tuple[str, ...]", ("read", "read", "read", "thumbnail", "write", "watch")),
        ("first", "str", "read"),
        ("union", "frozenset[str]", frozenset({"read", "thumbnail", "watch", "write"})),
    ],
)
def test_each_combine_and_kind(tmp_path, combine, kind, expected):
    api, _ = _client(tmp_path, [{**SCOPES, "combine": combine, "kind": kind}])
    assert api.__scopes__ == expected


def test_without_a_kind_it_is_inferred(tmp_path):
    _, module = _client(tmp_path, [{key: value for key, value in SCOPES.items() if key != "kind"}])
    assert "__scopes__: ClassVar[tuple[str, ...]] = ('read', 'thumbnail', 'watch', 'write')" in module


def test_a_directive_on_the_operation_itself_is_read_off_the_clients_documents(tmp_path):
    field = {"name": "__needs__", "collector": {"type": "operation_directive", "directive": "needs", "argument": "scopes"}}
    api, _ = _client(tmp_path, [field])
    assert api.__needs__ == ("extra",)


def combine_shortest(groups):
    """A combine of one's own: the scopes of the operation that needs the fewest."""
    return min(groups, key=len)


class CountingCollector(Collector):
    """A collector of one's own: one value per operation, its number of root fields."""

    type: str = "tests.test_class_fields.CountingCollector"
    target = "operation"

    def check(self, schema, registry):
        return None

    def element_annotation(self, schema, registry):
        return "int"

    def default_combine(self, schema):
        return "all"

    def collect_operation(self, schema, operation, fragments, registry):
        from turms.schema_lookup import root_field_nodes

        return (len(list(root_field_nodes(operation.selection_set, fragments))),)


def test_a_collector_and_a_combine_of_ones_own(tmp_path):
    shortest = {**SCOPES, "combine": "tests.test_class_fields.combine_shortest"}
    counting = {"name": "__roots__", "collector": {"type": "tests.test_class_fields.CountingCollector"}}
    api, _ = _client(tmp_path, [shortest, counting])
    assert api.__scopes__ == ("write",)
    assert api.__roots__ == (2, 1, 1, 1)


def test_a_type_collector_cannot_stamp_a_client_nor_an_operation_collector_a_type(tmp_path):
    with pytest.raises(GenerationError, match="collected per type"):
        _client(tmp_path, [{"name": "__x__", "collector": {"type": "type_directive", "directive": "auth"}}])
    with pytest.raises(RegistryError, match="collected per operation"):
        _generate(tmp_path, [SCOPES])


@pytest.mark.parametrize(
    ("combine", "kind"),
    [("union", "str"), ("first", "tuple[str, ...]")],
)
def test_a_kind_that_does_not_hold_what_the_combine_gives_is_refused(combine, kind):
    with pytest.raises(ValidationError, match="gives"):
        ClientPluginConfig(client_class="ImageApi", client_fields=[{**SCOPES, "combine": combine, "kind": kind}])


def test_a_combine_of_ones_own_needs_a_kind():
    with pytest.raises(ValidationError, match="needs the field's `kind`"):
        ClientPluginConfig(client_class="ImageApi", client_fields=[{**{k: v for k, v in SCOPES.items() if k != "kind"}, "combine": "tests.test_class_fields.combine_shortest"}])


def test_a_client_field_named_like_a_method_is_refused(tmp_path):
    with pytest.raises(GenerationError, match="both a class field and a method"):
        _client(tmp_path, [{**SCOPES, "name": "get"}])


def test_client_fields_refuse_an_introspected_schema(tmp_path):
    introspected = build_client_schema(introspection_from_schema(build_ast_schema(parse(client_sdl))))
    with pytest.raises(GenerationError, match="introspected"):
        _client(tmp_path, [SCOPES], schema=introspected)
