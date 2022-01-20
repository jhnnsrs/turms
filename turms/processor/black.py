from pydantic import BaseModel
from turms.processor.base import Processor


class BlackProcessorConfig(BaseModel):
    pass


class BlackProcessor(Processor):
    def __init__(self, config=None, **data):
        self.plugin_config = config or BlackProcessorConfig(**data)

    def run(self, gen_file: str):
        from black import format_str, FileMode

        return format_str(gen_file, mode=FileMode())
