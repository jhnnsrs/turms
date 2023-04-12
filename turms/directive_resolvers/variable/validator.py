import ast
from turms.registry import ClassRegistry
from graphql import VariableDefinitionNode

def validator(v: VariableDefinitionNode, body: list, registry: ClassRegistry, path: str):

    registry.register_import("pydantic.validator")
    registry.register_import(path)

    body.append(
                    ast.FunctionDef(
                        name=registry.generate_parameter_name(v.variable.name.value) + "_validator",
                        args=ast.arguments(
                            args=[
                                ast.arg(
                                    arg="cls",
                                ),
                                ast.arg(
                                    arg="value",
                                ),
                            ],
                            defaults=[],
                            kw_defaults=[],
                            kwarg=None,
                            kwonlyargs=[],
                            posonlyargs=[],
                            vararg=None,
                        ),
                        body=[
                            ast.Return(
                                value=ast.Call(
                                    func=ast.Name(id=path.split(".")[-1], ctx=ast.Load()),
                                    args=[ast.Name(id="cls", ctx=ast.Load()), ast.Name(id="value", ctx=ast.Load())],
                                    keywords=[],
                                ),
                            ),
                        ],
                        decorator_list=[
                            ast.Call(
                                    func=ast.Name(id="validator", ctx=ast.Load()),
                                    args=[
                                        ast.Constant(registry.generate_parameter_name(v.variable.name.value), ctx=ast.Load()),
                                    ],
                                    keywords=[
                                        ast.keyword(arg="pre", value=ast.Constant(True, ctx=ast.Load())),
                                        ast.keyword(arg="always", value=ast.Constant(True, ctx=ast.Load())),
                                    ],
                                ),
                        ],
                        returns=None,
                
                )
    )
    return body