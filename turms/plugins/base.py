from abc import abstractmethod
import ast
from optparse import Option
from typing import List, Optional

from pydantic import BaseSettings
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.registry import ClassRegistry


class PluginConfig(BaseSettings):
    type: Optional[str]


class Plugin:
    """Base Plugin Class

    Raises:
        NotImplementedError: [description]
    """

    @abstractmethod
    def generate_ast(
        self,
        config: GeneratorConfig,
        client_schema: GraphQLSchema,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        raise NotImplementedError("Plugin must overrwrite this")

    def __str__(self) -> str:
        return self.__class__.__name__
