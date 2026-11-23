from pydantic import Field

from turms.config import GeneratorConfig
from turms.processors.base import Processor, ProcessorConfig


class BlackProcessorConfig(ProcessorConfig):
    type: str = "turms.processors.black.BlackProcessor"


class BlackProcessor(Processor):
    """A processor that uses black to format the generated python code

    Black is a code formatter that is used to enforce a consistent style on the generated python code.
    It needs to be seperately installed via 'pip install black'.
    """

    config: BlackProcessorConfig = Field(default_factory=BlackProcessorConfig)

    def run(self, gen_file: str, config: GeneratorConfig) -> str:
        from black import FileMode, format_str

        return format_str(gen_file, mode=FileMode())
