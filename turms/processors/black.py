from pydantic import BaseModel
from rich import get_console
from turms.processors.base import Processor, ProcessorConfig


class BlackProcessorConfig(ProcessorConfig):
    type = "turms.processors.black.BlackProcessor"
    pass


class BlackProcessor(Processor):
    def __init__(self, config=None, **data):

        self.plugin_config = config or BlackProcessorConfig(**data)

    def run(self, gen_file: str):
        from black import format_str, FileMode

        return format_str(gen_file, mode=FileMode())
