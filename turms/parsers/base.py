from abc import abstractmethod
import ast
from typing import List, Optional
from pydantic import BaseModel, BaseSettings
from graphql.utilities.build_client_schema import GraphQLSchema


class ParserConfig(BaseSettings):
    type: str

    class Config:
        extra = "forbid"


class Parser(BaseModel):
    """Base Paser Class

    Raises:
        NotImplementedError: [description]
    """

    config: ParserConfig

    def parse_ast(
        self,
        asts: List[ast.AST],
    ) -> List[ast.AST]:
        raise NotImplementedError("Plugin must overrwrite this")
