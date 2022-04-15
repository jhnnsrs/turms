import subprocess
import os
import ast
import sys
from typing import List
from turms.run import write_code_to_file
import tempfile

DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative_glob(path):
    return DIR_NAME + path


class ExecuteError(Exception):
    pass


def unit_test_with(generated_ast: List[ast.AST], test_string: str):

    added_code = ast.parse(test_string).body

    md = ast.Module(body=generated_ast + added_code, type_ignores=[])

    # We need to unparse before otherwise there might be complaints with missing lineno
    parsed_code = ast.unparse(ast.fix_missing_locations(md))

    with tempfile.TemporaryDirectory() as tmpdirname:
        filename = write_code_to_file(parsed_code, tmpdirname, "minimal.py")
        s = subprocess.run([sys.executable, filename], capture_output=True)
        if s.returncode == 0:
            return True
        else:
            # If the supbrocess failed we can break out of the sandbox and just return the actual error
            raise ExecuteError(f"Failed with: {s.stderr.decode().strip()}")


def generated_module_is_executable(module: str) -> bool:
    exec_locals = {}
    exec_globals = {}

    imports = [line for line in module.split("\n") if line.startswith("from")]
    for import_ in imports:
        exec(import_, exec_globals, exec_locals)
    exec_globals.update(exec_locals)

    try:
        exec(module, exec_globals)
    except:
        return False
    return True
