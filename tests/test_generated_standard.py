"""Generated code meets the arkitekt Python standard.

The standard (``ruff.shared.toml`` in this repo, synced from arkitektio/.github)
asks for every argument and return to be annotated, no ``Any`` in a signature,
sorted imports, no unused ones, ``collections.abc`` over the deprecated
``typing`` aliases. A project on it runs turms with
``RuffProcessor(fix=True)``: ruff fixes what it can and fails on the rest, so
everything turms emits that ruff cannot fix (an unannotated method above all)
has to be right already.

Each case generates a module, runs it through the processor inside a directory
that carries the standard, and lints and format-checks the result there.
"""

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from graphql import GraphQLSchema, OperationType, build_ast_schema, parse

from turms.config import (
    FreezeConfig,
    GeneratorConfig,
    GraphQLTypes,
    OptionsConfig,
    PythonType,
    PythonVersion,
)
from turms.plugins.base import Plugin
from turms.plugins.client import ClientPlugin, ClientPluginConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.input_funcs import InputFuncsPlugin, InputFuncsPluginConfig
from turms.plugins.inputs import InputsPlugin, InputsPluginConfig
from turms.plugins.operations import OperationsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.processors.ruff import RuffProcessor, RuffProcessorConfig
from turms.run import build_schema_from_schema_type, generate_ast, parse_asts_to_string
from turms.stylers.default import DefaultStyler

from .utils import build_relative_glob, unit_test_with

REPO_ROOT = Path(__file__).resolve().parent.parent

requires_ruff = pytest.mark.skipif(
    shutil.which("ruff") is None, reason="ruff is not installed"
)

SCALARS = {
    name: PythonType(python)
    for name, python in {
        "uuid": "str",
        "Callback": "str",
        "Any": "typing.Any",
        "QString": "str",
    }.items()
}

DISCRIMINATED_SDL = """
directive @unionElementOf(union: String!, discriminator: String!, key: String!) repeatable on INPUT_OBJECT

input CpuInput @unionElementOf(union: "MachineInput", discriminator: "kind", key: "cpu") {
    cores: Int
}

input GpuInput @unionElementOf(union: "MachineInput", discriminator: "kind", key: "gpu") {
    vram: Int = 4
}

input MachineInput {
    kind: String!
    cores: Int
    vram: Int
}

type Query {
    hello(machine: MachineInput): String
}
"""


def schema(name: str) -> GraphQLSchema:
    return build_schema_from_schema_type(
        build_relative_glob(f"/schemas/{name}.graphql")
    )


def funcs() -> FuncsPlugin:
    return FuncsPlugin(
        config=FuncsPluginConfig(
            definitions=[
                FunctionDefinition(
                    type=OperationType.QUERY, use="mocks.query", is_async=False
                ),
                FunctionDefinition(
                    type=OperationType.QUERY, use="mocks.aquery", is_async=True
                ),
                FunctionDefinition(
                    type=OperationType.MUTATION, use="mocks.query", is_async=False
                ),
                FunctionDefinition(
                    type=OperationType.MUTATION, use="mocks.aquery", is_async=True
                ),
                FunctionDefinition(
                    type=OperationType.SUBSCRIPTION,
                    use="mocks.subscribe",
                    is_async=False,
                ),
                FunctionDefinition(
                    type=OperationType.SUBSCRIPTION,
                    use="mocks.asubscribe",
                    is_async=True,
                ),
            ]
        )
    )


def client() -> ClientPlugin:
    return ClientPlugin(
        config=ClientPluginConfig(
            client_class="Api",
            expand_input_types=[GraphQLTypes.INPUT],
        )
    )


def operations(last: Callable[[], Plugin]) -> list[Plugin]:
    return [
        EnumsPlugin(),
        InputsPlugin(),
        FragmentsPlugin(),
        OperationsPlugin(),
        last(),
    ]


def client_config(documents: str) -> GeneratorConfig:
    """A client project as the arkitekt clients configure it."""
    return GeneratorConfig(
        documents=build_relative_glob(documents),
        scalar_definitions=SCALARS,
        exclude_typenames=True,
        freeze=FreezeConfig(enabled=True),
        options=OptionsConfig(
            enabled=True,
            populate_by_name=True,
            alias_mode="split",
            use_enum_values=True,
            extra="forbid",
            types=[GraphQLTypes.INPUT],
        ),
    )


Case = tuple[GraphQLSchema, GeneratorConfig, list[Plugin]]


def case(name: str) -> Case:
    """The schema, config and plugins of one case, built when it runs."""
    if name == "arkitekt-funcs":
        return (
            schema("arkitekt"),
            GeneratorConfig(
                documents=build_relative_glob("/documents/arkitekt/**/*.graphql"),
                scalar_definitions=SCALARS,
            ),
            operations(funcs),
        )
    if name == "arkitekt-client":
        return (
            schema("arkitekt"),
            client_config("/documents/arkitekt/**/*.graphql"),
            operations(client),
        )
    if name == "beasts-client":
        # Subscriptions (iterators) and a schema without a single enum.
        return (
            schema("beasts"),
            client_config("/documents/beasts/*.graphql"),
            operations(client),
        )
    if name == "inputs-default-funcs":
        # Schema defaults (GraphQLDefault) and the UNSET sentinel.
        return (
            schema("nested_inputs"),
            GeneratorConfig(
                documents=build_relative_glob("/documents/inputs_default/*.graphql")
            ),
            operations(funcs),
        )
    if name == "oneof-client":
        # The @oneOf wire serializer.
        return (
            schema("oneof"),
            GeneratorConfig(
                documents=build_relative_glob("/documents/oneof/*.graphql")
            ),
            operations(client),
        )
    if name == "discriminated-input-funcs":
        # The discriminator's model_post_init.
        return (
            build_ast_schema(parse(DISCRIMINATED_SDL)),
            GeneratorConfig(),
            [
                InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False)),
                InputFuncsPlugin(
                    config=InputFuncsPluginConfig(skip_unreferenced=False)
                ),
            ],
        )
    if name == "builtin-strawberry":
        # The builtin introspection enums (`class __TypeKind(str, Enum)`).
        return schema("builtin"), GeneratorConfig(), [StrawberryPlugin()]
    raise AssertionError(name)


CASES = [
    "arkitekt-funcs",
    "arkitekt-client",
    "beasts-client",
    "inputs-default-funcs",
    "oneof-client",
    "discriminated-input-funcs",
    "builtin-strawberry",
]


@pytest.fixture
def standard_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A directory holding the standard, the processor's working directory."""
    shutil.copy(REPO_ROOT / "ruff.shared.toml", tmp_path / "ruff.shared.toml")
    (tmp_path / "ruff.toml").write_text(
        'extend = "ruff.shared.toml"\ntarget-version = "py310"\n'
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def ruff(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ruff", *args],
        capture_output=True,
        text=True,
    )


@requires_ruff
@pytest.mark.parametrize("name", CASES)
def test_generated_code_meets_the_standard(name: str, standard_dir: Path) -> None:
    client_schema, config, plugins = case(name)
    code = parse_asts_to_string(
        generate_ast(config, client_schema, stylers=[DefaultStyler()], plugins=plugins)
    )

    # Raises if ruff cannot fix everything it finds.
    processed = RuffProcessor(config=RuffProcessorConfig(fix=True, format=True)).run(
        code, config
    )

    generated = standard_dir / "schema.py"
    generated.write_text(processed)
    check = ruff("check", "--output-format", "concise", str(generated))
    assert check.returncode == 0, check.stdout + check.stderr
    formatted = ruff("format", "--check", str(generated))
    assert formatted.returncode == 0, formatted.stdout + formatted.stderr


def test_no_enum_import_without_an_enum() -> None:
    """The beasts schema declares no enum, so nothing imports Enum."""
    client_schema, config, plugins = case("beasts-client")
    code = parse_asts_to_string(
        generate_ast(config, client_schema, stylers=[DefaultStyler()], plugins=plugins)
    )
    assert "Enum" not in code


def test_builtin_enums_import_enum() -> None:
    """A builtin introspection enum brings its own import of Enum."""
    client_schema, config, plugins = case("builtin-strawberry")
    code = parse_asts_to_string(
        generate_ast(config, client_schema, stylers=[DefaultStyler()], plugins=plugins)
    )
    assert "class __TypeKind(str, Enum)" in code
    assert "from enum import Enum" in code


def test_iterators_come_from_collections_abc() -> None:
    client_schema, config, plugins = case("arkitekt-funcs")
    code = parse_asts_to_string(
        generate_ast(config, client_schema, stylers=[DefaultStyler()], plugins=plugins)
    )
    assert "from collections.abc import AsyncIterator, Iterator" in code
    assert "Iterator" not in next(
        line for line in code.splitlines() if line.startswith("from typing import")
    )


@pytest.mark.parametrize(
    ("version", "annotation"),
    [("3.9", "reason: 'str | None'=None"), ("3.10", "reason: str | None=None")],
)
def test_deprecated_marker_runs_on_its_target(
    version: PythonVersion, annotation: str
) -> None:
    """``str | None`` is quoted only where it would raise (before python 3.10)."""
    sdl = """
    type Query {
        hello(old: String @deprecated(reason: "use new")): String
        hello2: String
    }
    input LegacyInput {
        old: String @deprecated(reason: "use new")
        new: String
    }
    type Mutation {
        do(input: LegacyInput): String
    }
    """
    config = GeneratorConfig(min_python_version=version)
    generated = generate_ast(
        config,
        build_ast_schema(parse(sdl)),
        stylers=[DefaultStyler()],
        plugins=[InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False))],
    )
    assert annotation in parse_asts_to_string(generated)
    unit_test_with(generated, "assert repr(Deprecated('x')) == \"Deprecated('x')\"")
