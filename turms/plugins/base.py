from abc import abstractmethod
import ast
from optparse import Option
from typing import List, Optional

from pydantic import BaseModel, BaseSettings
from graphql.utilities.build_client_schema import GraphQLSchema


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
        raise NotImplementedError("Plugin must overrwrite this")
