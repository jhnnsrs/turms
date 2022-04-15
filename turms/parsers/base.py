import ast
from typing import List
from pydantic import BaseModel, BaseSettings


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
        ...  # pragma: no cover
