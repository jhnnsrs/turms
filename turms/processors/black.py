from pydantic import Field
from turms.processors.base import Processor, ProcessorConfig
from turms.config import GeneratorConfig


class BlackProcessorConfig(ProcessorConfig):
    type: str = "turms.processors.black.BlackProcessor"


class BlackProcessor(Processor):
    """A processor that uses black to format the generated python code

    Black is a code formatter that is used to enforce a consistent style on the generated python code.
    It needs to be seperately installed via 'pip install black'.
    """

    config: BlackProcessorConfig = Field(default_factory=BlackProcessorConfig)

    def run(self, gen_file: str, config: GeneratorConfig):
        from black import format_str, FileMode

        return format_str(gen_file, mode=FileMode())
