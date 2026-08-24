import ast
from abc import abstractmethod
from typing import List

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from turms.config import LogFunction, print_logger


class ParserConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


class Parser(BaseModel):
    """Base class for all parsers

    Parsers are used to parse the AST of the generated python code. They can be used to
    modify the AST before it is written to the file."""

    # LogFunction is a Protocol, so pydantic needs this to accept it as a field.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: ParserConfig

    #: turms passes this to every component it constructs (see turms.run);
    #: without the field pydantic would silently drop it.
    log: LogFunction = Field(default=print_logger)

    @abstractmethod
    def parse_ast(
        self,
        asts: List[ast.AST],
    ) -> List[ast.AST]:
        """Transform the generated AST and return it.

        The return value replaces the tree, so an implementation must return the
        (possibly modified) list -- returning ``None`` discards everything.
        """
        ...  # pragma: no cover
