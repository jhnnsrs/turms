from pydantic import Field
from turms.stylers.base import BaseStyler, StylerConfig
import re


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class DefaultStylerConfig(StylerConfig):
    type: str = "turms.stylers.default.DefaultStyler"


class DefaultStyler(BaseStyler):
    """A styler that does capitalize the first letter of the python class names
    and converts camelCase to snake_case for node and parameter names.  (e.g. camelCase -> camel_case)

    This is the default styler used for python projects"""

    config: DefaultStylerConfig = Field(default_factory=DefaultStylerConfig)

    def style_fragment_name(self, typename):
        return typename[0].upper() + typename[1:]

    def style_query_name(self, typename):
        return typename[0].upper() + typename[1:]

    def style_subscription_name(self, typename):
        return typename[0].upper() + typename[1:]

    def style_mutation_name(self, typename):
        return typename[0].upper() + typename[1:]

    def style_input_name(self, typename):
        return typename[0].upper() + typename[1:]

    def style_enum_name(self, typename):
        return typename[0].upper() + typename[1:]

    def style_node_name(self, name: str) -> str:
        return camel_to_snake(name)

    def style_parameter_name(self, name: str) -> str:
        return camel_to_snake(name)
