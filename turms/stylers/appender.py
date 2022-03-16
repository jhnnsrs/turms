from pydantic import BaseModel
from turms.stylers.base import BaseStyler, StylerConfig


class AppenderStylerConfig(StylerConfig):
    type = "turms.stylers.appender.AppenderStyler"
    append_fragment: str = "Fragment"
    append_query: str = "Query"
    append_mutation: str = "Mutation"
    append_subscription: str = "Subscription"
    append_enum: str = "Enum"
    append_input: str = "Input"


class AppenderStyler(BaseStyler):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config = AppenderStylerConfig(**kwargs)

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
