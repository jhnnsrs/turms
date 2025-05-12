import ast
from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ParserConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


class Parser(BaseModel):
    """Base class for all parsers

    Parsers are used to parse the AST of the generated python code. They can be used to
    modify the AST before it is written to the file."""

    def parse_ast(
        self,
        asts: List[ast.AST],
    ) -> List[ast.AST]: ...  # pragma: no cover
