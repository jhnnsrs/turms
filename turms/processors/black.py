from pydantic import BaseModel, Field
from rich import get_console
from turms.processors.base import Processor, ProcessorConfig


class BlackProcessorConfig(ProcessorConfig):
    type = "turms.processors.black.BlackProcessor"
    pass


class BlackProcessor(Processor):
    config: BlackProcessorConfig = Field(default_factory=BlackProcessorConfig)

    def run(self, gen_file: str):
        from black import format_str, FileMode

        return format_str(gen_file, mode=FileMode())
