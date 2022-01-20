from turms.processor.base import Processor


class BlackProcessor(Processor):
    def run(gen_file: str):
        from black import format_str, FileMode

        return format_str(gen_file, mode=FileMode())
