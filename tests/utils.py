import ast
import os
import subprocess
import sys
import tempfile
from textwrap import dedent
from typing import List

from turms.run import write_code_to_file

DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative_glob(path):
    return DIR_NAME + path



class ExecuteError(Exception):
    pass


mocks_code = """
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def query(model: Type[T], variables) -> T:
    return model(variables)  # pragma: nocover


async def aquery(model: Type[T], variables) -> T:
    return model(variables)  # pragma: nocover


def subscribe(model: Type[T], variables) -> T:
    yield model(variables)  # pragma: nocover
    yield model(variables)  # pragma: nocover


async def asubscribe(model: Type[T], variables) -> T:
    yield model(variables)  # pragma: nocover
    yield model(variables)  # pragma: nocover


class ExtraArguments(BaseModel):
    extra: Optional[str]


class ExtraOnOperations(BaseModel):
    extra: Optional[str]


class ExtraArg(BaseModel):
    extra: Optional[str]


class CustomDefault:
    def __init__(self, value):
        self.value = value


class CustomDeprecated:
    def __init__(self, reason=None):
        self.reason = reason


class CustomUnset:
    pass


CUSTOM_UNSET = CustomUnset()

"""


def parse_to_code(tree: List[ast.AST]) -> str:
    md = ast.Module(body=tree, type_ignores=[])
    return ast.unparse(ast.fix_missing_locations(md))


def find_type_checker():
    """Path to a pyright-compatible checker, or None.

    Looked up rather than assumed: the alias-mode guarantee is a *static* one, so
    the only test that can observe it needs a type checker, but turms must still
    be testable without one installed.
    """
    import shutil

    for name in ("basedpyright", "pyright"):
        found = shutil.which(name)
        if found:
            return found
    return None


def type_check_with(generated_ast: List[ast.AST], test_string: str):
    """Type-checks the generated module plus ``test_string`` and returns the
    diagnostics as a list of ``(line, message)``, line numbers being relative to
    ``test_string`` (0-based, as the checker reports them for the appended code).

    Returns None when no checker is installed, so callers can skip.

    This exists because ``populate_by_name`` is invisible to type checkers: a
    runtime test passes under both alias modes, so only a checker can tell them
    apart.
    """
    import json

    checker = find_type_checker()
    if checker is None:
        return None

    added_code = ast.parse(dedent(test_string)).body
    module_code = parse_to_code(generated_ast)
    probe_code = parse_to_code(added_code)

    with tempfile.TemporaryDirectory() as tmpdirname:
        write_code_to_file(module_code, tmpdirname, "generated_module.py")
        write_code_to_file(
            "from generated_module import *  # noqa: F403\n" + probe_code,
            tmpdirname,
            "probe.py",
        )
        s = subprocess.run(
            [checker, "--outputjson", os.path.join(tmpdirname, "probe.py")],
            capture_output=True,
            cwd=tmpdirname,
        )
        try:
            report = json.loads(s.stdout.decode())
        except json.JSONDecodeError:  # pragma: no cover
            raise ExecuteError(f"Type checker produced no JSON: {s.stdout.decode()[:2000]}")

    return [
        (d["range"]["start"]["line"], d["message"])
        for d in report.get("generalDiagnostics", [])
        if d.get("severity") == "error"
    ]


def unit_test_with(
    generated_ast: List[ast.AST], test_string: str, strict_warnings: bool = False
):

    added_code = ast.parse(dedent(test_string)).body
    # We need to unparse before otherwise there might be complaints with missing lineno
    parsed_code = parse_to_code(generated_ast + added_code)

    with tempfile.TemporaryDirectory() as tmpdirname:

        filename = write_code_to_file(parsed_code, tmpdirname, "minimal.py")
        write_code_to_file(mocks_code, tmpdirname, "mocks.py")
        argv = [sys.executable]
        if strict_warnings:
            argv += ["-W", "error::UserWarning"]
        s = subprocess.run(argv + [filename], capture_output=True)
        if s.returncode == 0:
            return True
        else:
            # If the supbrocess failed we can break out of the sandbox and just return the actual error
            raise ExecuteError(f"Failed with: {s.stderr.decode().strip()} Code: {parsed_code}" )
