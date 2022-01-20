from pydantic import BaseModel
from rich import get_console
from turms.processor.base import Processor


class BlackProcessorConfig(BaseModel):
    pass


class BlackProcessor(Processor):
    def __init__(self, config=None, **data):

        self.plugin_config = config or BlackProcessorConfig(**data)

    def run(self, gen_file: str):
        try:
            from black import format_str, FileMode

            return format_str(gen_file, mode=FileMode())
        except Exception as e:
            get_console().log(
                "Wasn't able to use the Blackprocessor. Please Make sure to install black."
            )

        return gen_file
