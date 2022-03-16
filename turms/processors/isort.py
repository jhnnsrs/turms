from pydantic import BaseModel
from rich import get_console
from turms.processors.base import Processor, ProcessorConfig


class IsortProcessorConfig(ProcessorConfig):
    type = "turms.processors.isort.IsortProcessor"
    pass


class IsortProcessor(Processor):
    def __init__(self, config=None, **data):
        self.plugin_config = config or IsortProcessorConfig(**data)

    def run(self, gen_file: str):
        import isort

        return isort.code(gen_file)
