from abc import abstractmethod
import ast
from typing import List

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.config import LogFunction


class PluginConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


class Plugin(BaseModel):
    """
    Base class for all plugins

    Plugins are the workhorse of turms. They are used to generate python code, according
    to the GraphQL schema. You can use plugins to generate python code for your GraphQL
    schema. THe all received the graphql schema and the config of the plugin."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    config: PluginConfig
    log: LogFunction = Field(default=lambda *args, **kwargs: print(*args))

    @abstractmethod
    def generate_ast(
        self,
        config,
        client_schema: GraphQLSchema,
        registry,
    ) -> List[ast.AST]: ...  # pragma: no cover
