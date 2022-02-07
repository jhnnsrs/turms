from pydantic import BaseModel
from rich import get_console
from turms.processor.base import Processor


class IsortProcessorConfig(BaseModel):
    pass


class IsortProcessor(Processor):
    def __init__(self, config=None, **data):
        self.plugin_config = config or IsortProcessorConfig(**data)

    def run(self, gen_file: str):
        try:
            import isort

            return isort.code(gen_file)
        except Exception as e:
            get_console().log(
                "Wasn't able to use the Blackprocessor. Please Make sure to install black."
            )

        return gen_file
