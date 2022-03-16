from pydantic import BaseModel, Field
from rich import get_console
from turms.processors.base import Processor, ProcessorConfig


class IsortProcessorConfig(ProcessorConfig):
    type = "turms.processors.isort.IsortProcessor"
    pass


class IsortProcessor(Processor):
    config: IsortProcessorConfig = Field(default_factory=IsortProcessorConfig)

    def run(self, gen_file: str):
        import isort

        return isort.code(gen_file)
