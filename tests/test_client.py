"""The client plugin: every operation as a method of one class that delegates
to ``execute``/``aexecute``/``subscribe``/``asubscribe`` of ``self``."""

import ast
from textwrap import dedent

import pytest
from pydantic import ValidationError

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.client import ClientPlugin, ClientPluginConfig, names_reserved_by
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.funcs import Kwarg
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from .utils import build_relative_glob, parse_to_code, unit_test_with

RECORDING_CLIENT = """
import asyncio
from types import SimpleNamespace

class Client(BeastApi):
    def __init__(self):
        self.calls = []

    def execute(self, model, variables):
        self.calls.append(("execute", model.__name__, variables))
        return SimpleNamespace(beasts=[], create_beast="created")

    async def aexecute(self, model, variables):
        self.calls.append(("aexecute", model.__name__, variables))
        return SimpleNamespace(beasts=[], create_beast="created")

    def subscribe(self, model, variables):
        self.calls.append(("subscribe", model.__name__, variables))
        yield SimpleNamespace(watch_beast="first")
        yield SimpleNamespace(watch_beast="second")

    async def asubscribe(self, model, variables):
        self.calls.append(("asubscribe", model.__name__, variables))
        yield SimpleNamespace(watch_beast="first")
        yield SimpleNamespace(watch_beast="second")

async def collect(agen):
    return [x async for x in agen]
"""


def generate(schema, **client_config):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/beasts/*.graphql"),
    )
    return generate_ast(
        config,
        schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
            ClientPlugin(
                config=ClientPluginConfig(client_class="BeastApi", **client_config)
            ),
        ],
    )


def method_names(generated, class_name="BeastApi"):
    module = ast.parse(parse_to_code(generated))
    assert not [
        n for n in module.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ], "no free functions are generated"
    (client,) = [
        n for n in module.body if isinstance(n, ast.ClassDef) and n.name == class_name
    ]
    return [
        n.name
        for n in client.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def test_operations_become_methods_delegating_to_self(beast_schema):
    generated = generate(beast_schema)
    assert sorted(method_names(generated)) == sorted(
        [
            "get_beasts",
            "aget_beasts",
            "create_beast",
            "acreate_beast",
            "watch_beast",
            "awatch_beast",
        ]
    )
    code = parse_to_code(generated)
    assert "import execute" not in code and "funcs" not in code
    assert "return self.execute(Get_beasts, variables).beasts" in code
    assert "return (await self.aexecute(Get_beasts, variables)).beasts" in code
    assert "for event in self.subscribe(WatchBeast, variables):" in code
    assert "async for event in self.asubscribe(WatchBeast, variables):" in code

    unit_test_with(
        generated,
        RECORDING_CLIENT
        + dedent("""
        c = Client()
        assert c.get_beasts() == []
        assert asyncio.run(c.aget_beasts()) == []
        assert c.create_beast("1", 4, "Canis", "Dog", "mammal") == "created"
        assert asyncio.run(c.acreate_beast("1", 4, "Canis", "Dog", "mammal")) == "created"
        assert list(c.watch_beast("1")) == ["first", "second"]
        assert asyncio.run(collect(c.awatch_beast("1"))) == ["first", "second"]
        assert [call[0] for call in c.calls] == [
            "execute", "aexecute", "execute", "aexecute", "subscribe", "asubscribe"
        ]
        assert c.calls[0][1:] == ("Get_beasts", {})
        assert c.calls[2][1] == "CreateBeast"
        assert c.calls[2][2]["commonName"] == "Dog"
        assert c.calls[4][1:] == ("WatchBeast", {"id": "1"})
        """),
    )


def test_delegate_names_are_configurable(beast_schema):
    generated = generate(
        beast_schema,
        execute="run",
        aexecute="arun",
        subscribe="stream",
        asubscribe="astream",
    )
    code = parse_to_code(generated)
    assert "self.run(" in code and "self.arun(" in code
    assert "self.stream(" in code and "self.astream(" in code
    assert "self.execute(" not in code


def test_only_the_requested_variants_are_generated(beast_schema):
    assert sorted(method_names(generate(beast_schema, sync_methods=False))) == sorted(
        ["aget_beasts", "acreate_beast", "awatch_beast"]
    )
    assert sorted(method_names(generate(beast_schema, async_methods=False))) == sorted(
        ["get_beasts", "create_beast", "watch_beast"]
    )


def test_at_least_one_variant_is_required():
    with pytest.raises(ValidationError, match="at least one"):
        ClientPluginConfig(client_class="X", sync_methods=False, async_methods=False)


def test_client_bases_are_imported_and_used(beast_schema):
    generated = generate(beast_schema, client_bases=["mocks.ExtraArguments"])
    code = parse_to_code(generated)
    assert "from mocks import" in code
    assert "class BeastApi(ExtraArguments):" in code


def test_a_base_can_provide_the_delegates(beast_schema):
    # The mixin is complete on its own once a base implements the delegates.
    generated = generate(beast_schema, client_bases=["mocks.RecordingExecutor"])
    unit_test_with(
        generated,
        """
        assert BeastApi().get_beasts() == ["from base"]
        """,
    )


def test_global_kwargs_are_forwarded_to_the_delegate(beast_schema):
    generated = generate(
        beast_schema, global_kwargs=[Kwarg(key="timeout", type="typing.Any")]
    )
    code = parse_to_code(generated)
    assert "def get_beasts(self, timeout: Any | None=None)" in code
    assert "self.execute(Get_beasts, variables, timeout=timeout)" in code


def test_reserved_method_name_is_refused(beast_schema):
    with pytest.raises(GenerationError, match="shadows a reserved name"):
        generate(beast_schema, reserved_names=["get_beasts"])


def test_an_operation_named_like_a_delegate_is_refused(beast_schema):
    # The method would replace the very executor it delegates to.
    with pytest.raises(GenerationError, match="shadows a reserved name"):
        generate(beast_schema, execute="get_beasts")


def test_duplicate_method_names_are_refused(beast_schema):
    # Both prefixes empty: the sync and async query collide on one name, which a
    # class would silently resolve in favour of the second.
    with pytest.raises(GenerationError, match="Two operations generate the method"):
        generate(beast_schema, prepend_async="")


def test_reserved_from_covers_attributes_and_pydantic_fields(beast_schema):
    # A pydantic field silently hides a same-named method (only a UserWarning),
    # so it must be refused at generation, as must a plain attribute.
    with pytest.raises(GenerationError, match="shadows a reserved name"):
        generate(
            beast_schema, reserved_from=["tests.utils_reserved.WithGetBeastsField"]
        )
    with pytest.raises(GenerationError, match="shadows a reserved name"):
        generate(
            beast_schema, reserved_from=["tests.utils_reserved.WithGetBeastsMethod"]
        )


def test_reserved_from_ignores_the_previous_generation_of_the_client(beast_schema):
    """Regenerating must not trip over the methods the client already mixes in."""
    generate(
        beast_schema,
        reserved_from=["tests.utils_reserved.ClientMixingInPreviousOutput"],
    )
    reserved = names_reserved_by(
        ["tests.utils_reserved.ClientMixingInPreviousOutput"], "BeastApi"
    )
    assert "for_task" in reserved and "get_beasts" not in reserved


@pytest.mark.parametrize("bad", ["Beast Api", "1Api", ""])
def test_client_class_must_be_an_identifier(bad):
    with pytest.raises(ValidationError, match="identifier"):
        ClientPluginConfig(client_class=bad)


def test_delegates_must_be_identifiers():
    with pytest.raises(ValidationError, match="identifier"):
        ClientPluginConfig(client_class="X", execute="self.execute")
