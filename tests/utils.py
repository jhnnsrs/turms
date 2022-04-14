import subprocess
import os
import ast
import sys
from typing import List
from turms.run import write_code_to_file

DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative_glob(path):
    return DIR_NAME + path


def unit_test_with(generated_ast: List[ast.AST], test_string: str):
    added_code = ast.parse(test_string).body
    md = ast.Module(body=generated_ast + added_code, type_ignores=[])
    generadet_info= ast.unparse(ast.fix_missing_locations(md))
    x = compile(generadet_info,"test", mode="exec")
    exec(x, globals(), globals())



