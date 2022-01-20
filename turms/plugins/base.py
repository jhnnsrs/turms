from abc import abstractmethod
import ast
from typing import List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema


class Plugin:
    """Base Plugin Class

    Raises:
        NotImplementedError: [description]
    """

    def generate_imports(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        return []

    @abstractmethod
    def generate_body(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        raise NotImplementedError("Plugin must overrwrite this")
