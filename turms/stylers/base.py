from abc import abstractmethod

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from turms.config import LogFunction, print_logger


class StylerConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


class Styler(BaseModel):
    """Base class for all stylers

    Stylers are used style the classnames function names of the generated python code.
    YOu can enforce specific code styles on the generated python code like (snake_case or camelCase)

    If you change the fieldname of a field in the GraphQL schema, the stylers will be used to
    style the fieldname in the generated python code and an alias will be added to the field.
    """

    # LogFunction is a Protocol, so pydantic needs this to accept it as a field.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: StylerConfig

    #: turms passes this to every component it constructs (see turms.run);
    #: without the field pydantic would silently drop it.
    log: LogFunction = Field(default=print_logger)

    @abstractmethod
    def style_subscription_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_mutation_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_query_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_enum_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_fragment_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_node_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_parameter_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_input_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover

    @abstractmethod
    def style_object_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")  # pragma: no cover


class BaseStyler(Styler):
    """A styler that uses no styling on the generated python code."""

    def style_query_name(self, name: str) -> str:
        return name

    def style_mutation_name(self, name: str) -> str:
        return name

    def style_enum_name(self, name: str) -> str:
        return name

    def style_fragment_name(self, name: str) -> str:
        return name

    def style_node_name(self, name: str) -> str:
        return name

    def style_input_name(self, name: str) -> str:
        return name

    def style_parameter_name(self, name: str) -> str:
        return name

    def style_subscription_name(self, name: str) -> str:
        return name

    def style_object_name(self, name: str) -> str:
        return name
