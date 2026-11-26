from pathlib import Path
from typing import NoReturn

import pytest

from turms.errors import GenerationError
from turms.plugins.operations import OperationsPlugin
from turms.run import gen


def test_create_file(tmp_path: Path, parsable_configs: list[str]) -> None:
    for config in parsable_configs:
        gen(config, overwrite_path=tmp_path)

        # gen() swallows exceptions unless strict=True, and write_code_to_file
        # truncates the target before writing -- so a failure here leaves an
        # empty file behind rather than raising. Assert on the content.
        written = list(tmp_path.glob("*.py"))
        assert written, f"{config} produced no output file"
        for path in written:
            assert path.stat().st_size > 0, f"{path} was truncated to empty"
            assert "class " in path.read_text(encoding="utf-8"), (
                f"{path} contains no generated classes"
            )


def test_create_file_faulty(
    tmp_path: Path, parsable_configs: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def faulty_parse(*args: object, **kwargs: object) -> NoReturn:
        raise Exception("Faulty parse")

    monkeypatch.setattr(OperationsPlugin, "generate_ast", faulty_parse)

    for config in parsable_configs:
        with pytest.raises(GenerationError):
            gen(config, overwrite_path=tmp_path, strict=True)
