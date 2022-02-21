from abc import abstractmethod


class Processor:
    @abstractmethod
    def run(gen_file: str):
        return gen_file

    def __str__(self) -> str:
        return self.__class__.__name__
