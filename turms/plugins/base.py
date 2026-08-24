from abc import abstractmethod
import ast
import warnings
from typing import Any, Sequence

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from graphql import GraphQLSchema
from turms.config import GeneratorConfig, LogFunction, print_logger  # noqa: F401
from turms.registry import ClassRegistry


class PluginConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


def rename_deprecated_keys(values: Any, renames: dict) -> Any:
    """Accept the old spelling of renamed plugin config keys, with a warning.

    Used by ``model_validator(mode="before")`` hooks on plugin configs. Done
    this way rather than with a pydantic validation alias because an alias on a
    ``BaseSettings`` field also replaces the ``TURMS_PLUGINS_*`` env-var name.
    """
    if not isinstance(values, dict):
        return values

    for old, new in renames.items():
        if old not in values:
            continue
        if new in values:
            raise ValueError(
                f"Set either '{new}' or its deprecated spelling '{old}', not both."
            )
        warnings.warn(
            f"'{old}' was renamed to '{new}' in turms 2.0; update your configuration.",
            DeprecationWarning,
            stacklevel=2,
        )
        values[new] = values.pop(old)

    return values


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
