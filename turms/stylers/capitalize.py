from pydantic import BaseModel, Field
from turms.stylers.base import BaseStyler


class CapitalizeSylerConfig(BaseModel):
    type: str = "turms.stylers.capitalize.CapitalizerSyler"
    capitalize_fragment: bool = True
    capitalize_query: bool = True
    capitalize_mutation: bool = True
    capitalize_subscription: bool = True
    capitalize_enum: bool = True
    capitalize_input: bool = True


class CapitalizeStyler(BaseStyler):
    """A styler that capitalizes the first letter of the python class names."""

    config: CapitalizeSylerConfig = Field(default_factory=CapitalizeSylerConfig)

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
