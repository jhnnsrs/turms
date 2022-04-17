from abc import abstractmethod
import ast
from typing import List, Union, Type, TypeVar, Tuple, Dict

from graphql import GraphQLNamedType
from pydantic import BaseModel, BaseSettings
from graphql.utilities.build_client_schema import GraphQLSchema

from turms.ast_generators import TypeAstGenerator

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
        return TypeAstGenerator.generate_type_description(gql_type.description)
