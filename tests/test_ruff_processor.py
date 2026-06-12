import shutil
import sys

import pytest

from turms.config import GeneratorConfig
from turms.processors.command import CommandProcessor, CommandProcessorConfig
from turms.processors.ruff import RuffProcessor, RuffProcessorConfig

UNFORMATTED = 'import os\nimport sys\nx={ "a":1,   "b":2}\ndef f( a,b ):\n  return a+b\n'

requires_ruff = pytest.mark.skipif(
    shutil.which("ruff") is None,
    reason="ruff is not installed",
)


# --- RuffProcessor -----------------------------------------------------------


@requires_ruff
def test_ruff_format():
    """Format-only run normalizes style but keeps the (unused) imports."""
    processor = RuffProcessor(config=RuffProcessorConfig())
    result = processor.run(UNFORMATTED, GeneratorConfig())

    assert "import os" in result
    assert '{"a": 1, "b": 2}' in result
    assert "def f(a, b):" in result


@requires_ruff
def test_ruff_fix_removes_unused_imports():
    """Enabling fix removes auto-fixable lint issues like unused imports."""
    processor = RuffProcessor(config=RuffProcessorConfig(fix=True))
    result = processor.run(UNFORMATTED, GeneratorConfig())

    assert "import os" not in result
    assert "import sys" not in result
    assert "def f(a, b):" in result


@requires_ruff
def test_ruff_no_op_when_everything_disabled():
    """Disabling both format and fix returns the code untouched."""
    processor = RuffProcessor(config=RuffProcessorConfig(format=False, fix=False))
    result = processor.run(UNFORMATTED, GeneratorConfig())

    assert result == UNFORMATTED


# --- CommandProcessor --------------------------------------------------------


def test_command_processor_plumbing_list():
    """Hermetic check of the stdin->stdout plumbing (no external tool needed).

    Pipes the code through a python one-liner that upper-cases it, so the test is
    deterministic and runs everywhere, including CI on every platform. List form is
    used so the (possibly backslash-containing) interpreter path is not shlex-split.
    """
    processor = CommandProcessor(
        config=CommandProcessorConfig(
            command=[
                sys.executable,
                "-c",
                "import sys; sys.stdout.write(sys.stdin.read().upper())",
            ]
        )
    )
    result = processor.run("def f(): pass\n", GeneratorConfig())

    assert result == "DEF F(): PASS\n"


def test_command_processor_raises_on_failure():
    """A non-zero exit from the command surfaces as a RuntimeError."""
    processor = CommandProcessor(
        config=CommandProcessorConfig(
            command=[sys.executable, "-c", "import sys; sys.exit(2)"]
        )
    )
    with pytest.raises(RuntimeError):
        processor.run(UNFORMATTED, GeneratorConfig())


@requires_ruff
def test_command_processor_with_ruff():
    """End-to-end: run ruff as the external command via the generic processor."""
    processor = CommandProcessor(
        config=CommandProcessorConfig(command="ruff format -")
    )
    result = processor.run(UNFORMATTED, GeneratorConfig())

    assert "def f(a, b):" in result
