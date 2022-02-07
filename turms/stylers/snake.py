from turms.stylers.base import BaseStyler
import re


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class SnakeNodeName(BaseStyler):
    def style_node_name(self, name: str) -> str:
        return camel_to_snake(name)
