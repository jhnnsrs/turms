from pydantic import Field
from turms.stylers.base import BaseStyler, StylerConfig
from turms.utils import capitalize_first


class CapitalizeStylerConfig(StylerConfig):
    type: str = "turms.stylers.capitalize.CapitalizeStyler"

class CapitalizeStyler(BaseStyler):
    """A styler that capitalizes the first letter of the python class names."""

    config: CapitalizeStylerConfig = Field(default_factory=CapitalizeStylerConfig)

    def style_fragment_name(self, typename):
        return capitalize_first(typename)

    def style_query_name(self, typename):
        return capitalize_first(typename)

    def style_subscription_name(self, typename):
        return capitalize_first(typename)

    def style_mutation_name(self, typename):
        return capitalize_first(typename)

    def style_input_name(self, typename):
        return capitalize_first(typename)

    def style_enum_name(self, typename):
        return capitalize_first(typename)
