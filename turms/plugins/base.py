from abc import abstractmethod
import ast
from typing import List

from pydantic import BaseModel, BaseSettings
from graphql.utilities.build_client_schema import GraphQLSchema


class PluginConfig(BaseSettings):
    type: str

    class Config:
        extra = "forbid"


class Plugin(BaseModel):
    """
    Base class for all plugins

    Plugins are the workhorse of turms. They are used to generate python code, according
    to the GraphQL schema. You can use plugins to generate python code for your GraphQL
    schema. THe all received the graphql schema and the config of the plugin."""

    config: PluginConfig

    @abstractmethod
    def generate_ast(
        self,
        config,
        client_schema: GraphQLSchema,
        registry,
    ) -> List[ast.AST]:
        ...  # pragma: no cover
