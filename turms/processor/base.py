from abc import abstractmethod


class Processor:
    @abstractmethod
    def run(gen_file: str):
        return gen_file
