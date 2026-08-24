from abc import abstractmethod

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from turms.config import GeneratorConfig, LogFunction, print_logger


class ProcessorConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid")
    type: str


class Processor(BaseModel):
    """Base class for all processors

    Processors are used to modify the generated python code before it is written to the file.
    You can use processors to enforce specific styles on the generated python code like (black
    or isort) or to add additional code to the generated python code.
    """

    # LogFunction is a Protocol, so pydantic needs this to accept it as a field.
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: ProcessorConfig

    #: turms passes this to every component it constructs (see turms.run);
    #: without the field pydantic would silently drop it.
    log: LogFunction = Field(default=print_logger)

    @abstractmethod
    def run(self, gen_file: str, config: GeneratorConfig) -> str:
        """Transform the generated source and return it.

        ``gen_file`` is the generated module as a string, not a path.
        """
        ...  # pragma: no cover
