from pydantic import Field
from turms.stylers.base import BaseStyler, StylerConfig


class AppenderStylerConfig(StylerConfig):
    type: str = "turms.stylers.appender.AppenderStyler"
    append_fragment: str = "Fragment"
    append_query: str = "Query"
    append_mutation: str = "Mutation"
    append_subscription: str = "Subscription"
    append_enum: str = ""
    append_input: str = ""


class AppenderStyler(BaseStyler):
    config: AppenderStylerConfig = Field(default_factory=AppenderStylerConfig)

    def style_fragment_name(self, typename):
        return f"{typename}{self.config.append_fragment}"

    def style_query_name(self, typename):
        return f"{typename}{self.config.append_query}"

    def style_subscription_name(self, typename):
        return f"{typename}{self.config.append_subscription}"

    def style_mutation_name(self, typename):
        return f"{typename}{self.config.append_mutation}"

    def style_input_name(self, typename):
        return f"{typename}{self.config.append_input}"

    def style_enum_name(self, typename):
        return f"{typename}{self.config.append_enum}"
