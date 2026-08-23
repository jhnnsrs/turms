"""Tests covering the python versions turms runs on and can target.

Two separate things carry a version number and drift apart easily:

* the interpreters turms itself is supported on -- declared by the trove
  classifiers in ``pyproject.toml`` and exercised by the CI matrix,
* the interpreters generated code may be targeted at -- the ``PythonVersion``
  literal, shared by ``GeneratorConfig.min_python_version`` and the polyfill
  parser.

These tests pin both down so adding a new python release means touching one
list, not four.
"""

import ast
import re
import sys
from pathlib import Path
from typing import get_args

import pytest
from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig, PythonVersion, parse_python_version
from turms.parsers.polyfill import (
    SUPPORTED_PYTHON_VERSIONS,
    PolyfillParser,
    PolyfillPluginConfig,
)
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from .utils import parse_to_code

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The python versions turms itself is supported on.
SUPPORTED_HOST_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


schema_sdl = """
input FilterInput {
    limit: Int = 10
    tags: [String!]
}

type Country {
    code: String
    name: String!
    friends: [Country!]
}

type Query {
    countries(filter: FilterInput): [Country!]!
}
"""


def generate(**config_kwargs):
    config = GeneratorConfig(**config_kwargs)
    return generate_ast(
        config,
        build_ast_schema(parse(schema_sdl)),
        stylers=[DefaultStyler()],
        plugins=[InputsPlugin(), ObjectsPlugin()],
    )


# --------------------------------------------------------------------------- #
# the interpreters turms runs on
# --------------------------------------------------------------------------- #


def _pyproject() -> str:
    return (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_classifiers_declare_every_supported_host_version():
    """Every interpreter we test on is advertised on PyPI, and no more."""
    declared = re.findall(
        r'"Programming Language :: Python :: (\d+\.\d+)"', _pyproject()
    )
    assert declared == SUPPORTED_HOST_VERSIONS


def test_ci_matrix_covers_every_supported_host_version():
    """A version nobody runs the suite on is not actually supported."""
    workflow = (REPO_ROOT / ".github/workflows/tests.yaml").read_text(encoding="utf-8")
    matrix = re.search(r"python-version: \[([^\]]*)\]", workflow)
    assert matrix, "no python-version matrix found in the CI workflow"
    versions = re.findall(r"\d+\.\d+", matrix.group(1))
    assert versions == SUPPORTED_HOST_VERSIONS


def test_running_interpreter_is_supported():
    """Guards against the suite quietly running on an undeclared interpreter."""
    running = "{}.{}".format(*sys.version_info[:2])
    assert running in SUPPORTED_HOST_VERSIONS


def test_requires_python_matches_the_oldest_supported_version():
    match = re.search(r'requires-python = ">=(\d+\.\d+)"', _pyproject())
    assert match
    assert match.group(1) == SUPPORTED_HOST_VERSIONS[0]


def test_outbound_tests_only_run_on_the_coverage_path():
    """The tests marked `network` must stay off the matrix and on in coverage.

    The matrix runs the same tests on five interpreters times two operating
    systems; pointing ten concurrent jobs at an IP-rate-limited API is what made
    them flaky. Coverage is a single job, so it can afford to run them -- and has
    to, or the introspection code paths go unmeasured.
    """
    matrix = (REPO_ROOT / ".github/workflows/tests.yaml").read_text(encoding="utf-8")
    coverage = (REPO_ROOT / ".github/workflows/coverage.yaml").read_text(
        encoding="utf-8"
    )
    assert 'pytest -m "not network"' in matrix
    assert "not network" not in coverage


def test_toml_configs_load_without_a_third_party_parser():
    """TOML support must not depend on a package that only happens to be around.

    On 3.11+ this is stdlib ``tomllib``, on 3.10 the declared ``tomli``
    backport -- either way loading a TOML config may not raise.
    """
    from turms.run import toml_loader

    class _Reader:
        def read(self):
            return 'name = "turms"\n'

    assert toml_loader(_Reader()) == {"name": "turms"}


# --------------------------------------------------------------------------- #
# the interpreters generated code can target
# --------------------------------------------------------------------------- #


def test_generator_and_polyfill_accept_the_same_versions():
    assert SUPPORTED_PYTHON_VERSIONS == get_args(PythonVersion)


def test_every_supported_host_version_is_targetable():
    """You can always target the interpreter you are generating on."""
    for version in SUPPORTED_HOST_VERSIONS:
        assert version in get_args(PythonVersion)


@pytest.mark.parametrize("version", get_args(PythonVersion))
def test_target_version_is_accepted_everywhere(version):
    assert GeneratorConfig(min_python_version=version).min_python_version == version
    assert PolyfillPluginConfig(python_version=version).python_version == version
    # a version that parses into a comparable tuple is a version the annotation
    # style can be resolved against
    assert parse_python_version(version) >= (3, 7)


@pytest.mark.parametrize("version", ["3.6", "4.0", "nonsense"])
def test_unknown_target_version_is_rejected_everywhere(version):
    with pytest.raises(Exception):
        GeneratorConfig(min_python_version=version)
    with pytest.raises(Exception):
        PolyfillPluginConfig(python_version=version)


@pytest.mark.parametrize("version", ["3.13", "3.14"])
def test_recent_targets_generate_modern_annotations(version):
    """3.13 and 3.14 are past both PEP 585 and PEP 604, so `auto` is modern."""
    config = GeneratorConfig(min_python_version=version)
    assert config.use_builtin_generics is True
    assert config.use_union_operator is True

    code = parse_to_code(generate(min_python_version=version))
    assert "tags: list[str] | None" in code
    assert "code: str | None" in code
    assert "Optional[" not in code
    assert "List[" not in code


@pytest.mark.parametrize("version", ["3.13", "3.14"])
def test_recent_targets_generate_importable_code(version):
    """The output has to be valid syntax for the interpreter running it."""
    code = parse_to_code(generate(min_python_version=version))
    compile(code, "<generated>", "exec")


@pytest.mark.parametrize("version", ["3.13", "3.14"])
def test_polyfill_is_a_noop_for_recent_targets(version):
    """Nothing needs backporting on a modern target -- the tree passes through."""
    tree = generate(min_python_version=version)
    parser = PolyfillParser(config=PolyfillPluginConfig(python_version=version))
    assert parse_to_code(parser.parse_ast(tree)) == parse_to_code(tree)


def test_polyfill_still_backports_for_old_targets():
    """Sharing the version list with the generator must not disarm the 3.7 path."""
    tree = ast.parse("from typing import Literal, Optional").body
    parser = PolyfillParser(config=PolyfillPluginConfig(python_version="3.7"))
    generated = parse_to_code(parser.parse_ast(tree))
    assert "from typing_extensions import Literal" in generated
    assert "from typing import Optional" in generated
    ast.parse(generated)
