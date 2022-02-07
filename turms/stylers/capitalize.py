from pydantic import BaseModel
from turms.stylers.base import BaseStyler


class Capitalizer(BaseStyler):
    def __init__(self, **kwargs) -> None:
        super().__init__()

    def style_fragment_name(self, typename):
        return typename.capitalize()

    def style_query_name(self, typename):
        return typename.capitalize()

    def style_subscription_name(self, typename):
        return typename.capitalize()

    def style_mutation_name(self, typename):
        return typename.capitalize()

    def style_input_name(self, typename):
        return typename.capitalize()

    def style_enum_name(self, typename):
        return typename.capitalize()
