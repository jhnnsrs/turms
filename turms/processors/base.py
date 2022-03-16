from abc import abstractmethod
from typing import Optional

from pydantic import BaseModel, BaseSettings


class ProcessorConfig(BaseSettings):
    type: str

    class Config:
        extra = "forbid"


class Processor(BaseModel):
    config: ProcessorConfig

    @abstractmethod
    def run(gen_file: str):
        return gen_file
