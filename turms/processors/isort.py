from pydantic import Field
from turms.processors.base import Processor, ProcessorConfig
from turms.config import GeneratorConfig


class IsortProcessorConfig(ProcessorConfig):
    type: str = "turms.processors.isort.IsortProcessor"


class IsortProcessor(Processor):
    """A processor that uses isort to format the generated python code
    imports in a specific order.

    """

    config: IsortProcessorConfig = Field(default_factory=IsortProcessorConfig)

    def run(self, gen_file: str, config: GeneratorConfig):
        import isort

        return isort.code(gen_file)
