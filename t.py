import ast

with open("l.py", "r") as f:
    old_code = f.read()


l = ast.parse(old_code)
5
