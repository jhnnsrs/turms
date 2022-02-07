from pydantic import BaseModel
from turms.stylers.base import BaseStyler


class AppenderConfig(BaseModel):
    append_fragment: str = "Fragment"
    append_query: str = "Query"
    append_mutation: str = "Mutation"
    append_subscription: str = "Subscription"
    append_enum: str = "Enum"
    append_input: str = "Input"


class Appender(BaseStyler):
    def __init__(self, **kwargs) -> None:
        super().__init__()
        self.config = AppenderConfig(**kwargs)

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
