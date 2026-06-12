import subprocess
import sys

from pydantic import Field
from turms.processors.base import Processor, ProcessorConfig
from turms.config import GeneratorConfig


class RuffProcessorConfig(ProcessorConfig):
    type: str = "turms.processors.ruff.RuffProcessor"
    format: bool = True
    """Whether to run `ruff format` to enforce a consistent style."""
    fix: bool = False
    """Whether to run `ruff check --fix` to apply auto-fixable lint rules (e.g. removing unused imports)."""


class RuffProcessor(Processor):
    """A processor that uses ruff to format and/or fix the generated python code.

    Ruff is an extremely fast python linter and code formatter. It needs to be
    separately installed via 'pip install ruff'.

    To run ruff on-demand (e.g. via uvx) without installing it as a dependency, use the
    generic `turms.processors.command.CommandProcessor` with `command: "uvx ruff format -"`.
    """

    config: RuffProcessorConfig = Field(default_factory=RuffProcessorConfig)

    def _run_ruff(self, args, gen_file: str) -> str:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", *args, "-"],
            input=gen_file,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"ruff {' '.join(args)} failed (exit code {result.returncode}):\n{result.stderr}"
            )
        return result.stdout

    def run(self, gen_file: str, config: GeneratorConfig):
        if self.config.fix:
            gen_file = self._run_ruff(
                ["check", "--fix", "--quiet", "--stdin-filename", "generated.py"],
                gen_file,
            )
        if self.config.format:
            gen_file = self._run_ruff(
                ["format", "--quiet", "--stdin-filename", "generated.py"],
                gen_file,
            )
        return gen_file
