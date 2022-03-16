from abc import abstractmethod
import ast
from typing import List, Optional
from pydantic import BaseModel, BaseSettings
from graphql.utilities.build_client_schema import GraphQLSchema


class ParserConfig(BaseSettings):
    type: str

    class Config:
        extra = "allow"


class Parser:
    """Base Paser Class

    Raises:
        NotImplementedError: [description]
    """

    plugin_config: ParserConfig

    def parse_ast(
        self,
        asts: List[ast.AST],
    ) -> List[ast.AST]:
        raise NotImplementedError("Plugin must overrwrite this")

    def __str__(self) -> str:
        return self.__class__.__name__
