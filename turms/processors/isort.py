from pydantic import Field
from turms.processors.base import Processor, ProcessorConfig


class IsortProcessorConfig(ProcessorConfig):
    type = "turms.processors.isort.IsortProcessor"


class IsortProcessor(Processor):
    config: IsortProcessorConfig = Field(default_factory=IsortProcessorConfig)

    def run(self, gen_file: str):
        import isort

        return isort.code(gen_file)
