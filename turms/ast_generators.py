import ast
from typing import Optional, List


class TypeAstGenerator:
    @staticmethod
    def _generate_description(description: str) -> ast.Expr:
        return ast.Expr(value=ast.Constant(value=description))

    @staticmethod
    def generate_type_description(
            description: str
    ) -> ast.Expr:
        return TypeAstGenerator._generate_description(description)

    @staticmethod
    def generate_field_description(
            description: str
    ) -> ast.Expr:
        return TypeAstGenerator._generate_description(description)

    @staticmethod
    def generate_class_definition(
            classname: str,
            base_classes: List[str],
            body: List[ast.AST]
    ) -> ast.ClassDef:
        return ast.ClassDef(
            classname,
            bases=[
                ast.Name(id=base.rsplit(".", maxsplit=1)[-1], ctx=ast.Load())
                for base in base_classes
            ],
            decorator_list=[],
            keywords=[],
            body=body,
        )


class EnumTypeAstGenerator(TypeAstGenerator):
    @staticmethod
    def generate_enum_value(
            field_name: str,
            enum_value: str
    ) -> ast.Assign:
        return ast.Assign(
            targets=[ast.Name(id=field_name, ctx=ast.Store())],
            value=ast.Constant(value=enum_value)
        )


class InputTypeAstGenerator(TypeAstGenerator):
    @staticmethod
    def generate_attribute(
            name: str,
            annotation: ast.AST,
            alias: Optional[ast.Call] = None
    ) -> ast.AnnAssign:
        return ast.AnnAssign(
            target=ast.Name(name, ctx=ast.Store()),
            annotation=annotation,
            value=alias,
            simple=1
        )

    @staticmethod
    def generate_field_alias(original_name: str) -> ast.Call:
        return ast.Call(
            func=ast.Name(id="Field", ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(arg="alias", value=ast.Constant(value=original_name))
            ]
        )


class AnnotationAstGenerator:
    @staticmethod
    def reference(typename: str) -> ast.Name:
        return ast.Name(id=typename, ctx=ast.Load())

    @staticmethod
    def forward_reference(typename: str) -> ast.Constant:
        return ast.Constant(value=typename, ctx=ast.Load())

    @staticmethod
    def optional(value: ast.AST) -> ast.Subscript:
        return AnnotationAstGenerator._wrap("Optional", value)

    @staticmethod
    def list(value: ast.AST) -> ast.Subscript:
        return AnnotationAstGenerator._wrap("List", value)

    @staticmethod
    def _wrap(outside: str, inside: ast.AST):
        return ast.Subscript(value=ast.Name(outside, ctx=ast.Load()),
                             slice=inside,
                             ctx=ast.Load())
