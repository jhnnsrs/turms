import pytest
from turms.plugins.operations import OperationsPlugin
from turms.run import gen
from turms.errors import GenerationError


def test_create_file(tmp_path, parsable_configs):
    for config in parsable_configs:
        gen(config, overwrite_path=tmp_path)


def test_create_file_faulty(tmp_path, parsable_configs, monkeypatch):
    def faulty_parse(*args, **kwargs):
        raise Exception("Faulty parse")

    monkeypatch.setattr(OperationsPlugin, "generate_ast", faulty_parse)

    for config in parsable_configs:
        with pytest.raises(GenerationError):
            gen(config, overwrite_path=tmp_path, strict=True)
