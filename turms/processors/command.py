import shlex
import subprocess

from turms.config import GeneratorConfig
from turms.processors.base import Processor, ProcessorConfig


class CommandProcessorConfig(ProcessorConfig):
    type: str = "turms.processors.command.CommandProcessor"
    command: str | list[str]
    """The command to run. The generated code is piped to the command's stdin and the
    formatted code is read back from its stdout. Can be given as a single string (parsed
    with shell-like splitting) or as a list of arguments.

    Examples:
        "ruff format -"
        ["uvx", "ruff", "format", "-"]
        "uvx black -"
    """


class CommandProcessor(Processor):
    """A processor that pipes the generated python code through an arbitrary command.

    The generated code is sent to the command's stdin and the (post)processed code is read
    back from its stdout. This is a generic escape hatch to run any external formatter or
    tool without a dedicated processor, e.g. running ruff via uvx:

        processors:
          - type: turms.processors.command.CommandProcessor
            command: "uvx ruff format -"
    """

    config: CommandProcessorConfig

    def run(self, gen_file: str, config: GeneratorConfig) -> str:
        command = self.config.command
        if isinstance(command, str):
            command = shlex.split(command)

        result = subprocess.run(
            command,
            input=gen_file,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Command {' '.join(command)} failed (exit code {result.returncode}):\n{result.stderr}"
            )
        return result.stdout
