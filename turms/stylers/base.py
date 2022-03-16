from abc import abstractmethod

from pydantic import BaseModel, BaseSettings


class StylerConfig(BaseSettings):
    type: str

    class Config:
        extra = "forbid"


class Styler(BaseModel):
    config: StylerConfig

    @abstractmethod
    def style_subscription_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_mutation_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_query_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_enum_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_fragment_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_node_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_parameter_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_input_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")


class BaseStyler(Styler):
    def style_operation_name(self, name: str) -> str:
        return name

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
