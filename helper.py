import ast


x = """

class lala(object):
    from_: int = Field(alias="from")





"""

print(ast.dump(ast.parse(x), indent=4))