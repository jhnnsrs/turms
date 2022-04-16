from abc import abstractmethod
import ast
from typing import List, Union, Type, TypeVar, Tuple, Dict, Optional

from graphql import GraphQLNamedType
from pydantic import BaseModel, BaseSettings
from graphql.utilities.build_client_schema import GraphQLSchema

GNT = TypeVar("GNT", bound=GraphQLNamedType)


class PluginConfig(BaseSettings):
    type: str

    class Config:
        extra = "forbid"


class Plugin(BaseModel):
    """Base Plugin Class

    Raises:
        NotImplementedError: [description]
    """

    config: PluginConfig

    @abstractmethod
    def generate_ast(
        self,
        config,
        client_schema: GraphQLSchema,
        registry,
    ) -> List[ast.AST]:
        ...  # pragma: no cover

    @staticmethod
    def _get_types_from_schema(
            client_schema: GraphQLSchema,
            class_or_tuple: Union[Type[GNT], Tuple[Type[GNT]]],
    ) -> Dict[str, GNT]:
        return {
            key: value
            for key, value in client_schema.type_map.items()
            if isinstance(value, class_or_tuple)
        }

    @staticmethod
    def _type_has_description(gql_type: GraphQLNamedType) -> bool:
        return gql_type.description is not None

    @staticmethod
    def _generate_type_description_ast(gql_type: GraphQLNamedType) -> ast.Expr:
        return AstGenerator.generate_type_description(gql_type.description)


class AstGenerator:
    @staticmethod
    def _generate_description(description: str) -> ast.Expr:
        return ast.Expr(value=ast.Constant(value=description))

    @staticmethod
    def generate_type_description(
            description: str
    ) -> ast.Expr:
        return AstGenerator._generate_description(description)

    @staticmethod
    def generate_field_description(
            description: str
    ) -> ast.Expr:
        return AstGenerator._generate_description(description)

    @staticmethod
    def generate_field_alias(original_name: str) -> ast.Call:
        return ast.Call(
            func=ast.Name(id="Field", ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(arg="alias", value=ast.Constant(value=original_name))
            ]
        )

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
    def generate_enum_value(
            field_name: str,
            enum_value: str
    ) -> ast.Assign:
        return ast.Assign(
            targets=[ast.Name(id=field_name, ctx=ast.Store())],
            value=ast.Constant(value=enum_value)
        )

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
