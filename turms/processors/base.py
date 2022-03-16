from abc import abstractmethod
from typing import Optional

from pydantic import BaseSettings


class ProcessorConfig(BaseSettings):
    type: str

    class Config:
        extra = "allow"


class Processor:
    @abstractmethod
    def run(gen_file: str):
        return gen_file

    def __str__(self) -> str:
        return self.__class__.__name__
