from abc import abstractmethod
import ast
from typing import List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.registry import ClassRegistry


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
