import ast
from pydantic import BaseModel
from enum import Enum
import libcst as cst

# the one we want to merge into
# load beast_two.py as a ast.Module
with open("beast_two.py") as f:
    existing_module = cst.parse_module(f.read())

# load beasts.py as a ast.Module

# the one we want to merge from
with open("beasts.py") as f:
    new_module = ast.parse(f.read())

print(existing_module)
