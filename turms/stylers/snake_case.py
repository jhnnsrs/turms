from pydantic import Field
from turms.stylers.base import BaseStyler, StylerConfig
import re


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class SnakeCaseStylerConfig(StylerConfig):
    type: str = "turms.stylers.snake_case.SnakeCaseStyler"


class SnakeCaseStyler(BaseStyler):
    """A styler that snake cased node and parameter names.  (e.g. camelCase -> camel_case)"""

    config: SnakeCaseStylerConfig = Field(default_factory=SnakeCaseStylerConfig)

    def style_node_name(self, name: str) -> str:
        return camel_to_snake(name)

    def style_parameter_name(self, name: str) -> str:
        return camel_to_snake(name)
