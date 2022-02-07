from abc import abstractmethod


class Styler:
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
    def style_fragment_class_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_node_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")

    @abstractmethod
    def style_input_name(self, name: str) -> str:
        raise NotImplementedError("Plugin must overrwrite this")


class BaseStyler(Styler):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

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
