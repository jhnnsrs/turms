from abc import abstractmethod
import ast
from typing import List, TYPE_CHECKING, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from graphql import GraphQLSchema
from turms.config import GeneratorConfig, LogFunction

from turms.config import GeneratorConfig
from turms.registry import ClassRegistry


class PluginConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


def print_logger(
    message: str,
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
) -> None:
    print(f"[{level}] {message}")


class Plugin(BaseModel):
    """
    Base class for all plugins

    Plugins are the workhorse of turms. They are used to generate python code, according
    to the GraphQL schema. You can use plugins to generate python code for your GraphQL
    schema. THe all received the graphql schema and the config of the plugin."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    log: LogFunction = Field(default=print_logger)

    @abstractmethod
    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> Sequence[ast.AST]: ...  # pragma: no cover
