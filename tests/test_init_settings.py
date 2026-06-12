import os

import yaml
from click.testing import CliRunner

from turms.cli import main as cli_main


def _turms_section(settings: str):
    config = yaml.safe_load(settings)
    return config["projects"]["default"]["extensions"]["turms"]


def _processors(settings: str):
    return [p["type"] for p in _turms_section(settings).get("processors", [])]


def _plugins(settings: str):
    return [p["type"] for p in _turms_section(settings)["plugins"]]


def test_documents_template_is_default():
    assert cli_main.build_default_settings() == cli_main.build_default_settings(
        "documents"
    )


def test_documents_template_includes_installed_formatters():
    """black and isort are dev dependencies, so the scaffold includes both."""
    processors = _processors(cli_main.build_default_settings("documents"))

    assert "turms.processors.black.BlackProcessor" in processors
    assert "turms.processors.isort.IsortProcessor" in processors


def test_documents_template_skips_missing_formatters(monkeypatch):
    """Without black/isort installed, no processors section is scaffolded."""
    monkeypatch.setattr(cli_main.importlib.util, "find_spec", lambda name: None)

    settings = cli_main.build_default_settings("documents")

    assert _processors(settings) == []
    assert "processors" not in settings


def test_documents_template_partial_install(monkeypatch):
    """Only the processor whose tool is installed is scaffolded."""
    monkeypatch.setattr(
        cli_main.importlib.util,
        "find_spec",
        lambda name: object() if name == "black" else None,
    )

    processors = _processors(cli_main.build_default_settings("documents"))

    assert processors == ["turms.processors.black.BlackProcessor"]


def test_documents_template_core_shape():
    turms = _turms_section(cli_main.build_default_settings("documents"))
    plugin_types = [p["type"] for p in turms["plugins"]]

    assert turms["out_dir"] == "api"
    assert "turms.plugins.enums.EnumsPlugin" in plugin_types
    assert "turms.plugins.operations.OperationsPlugin" in plugin_types
    assert turms["scalar_definitions"] == {"uuid": "str"}


def test_rath_template_adds_funcs_plugin():
    settings = cli_main.build_default_settings("rath")
    turms = _turms_section(settings)
    funcs = turms["plugins"][-1]

    assert funcs["type"] == "turms.plugins.funcs.FuncsPlugin"
    assert funcs["global_kwargs"][0]["type"] == "rath.Rath"
    async_definitions = [d for d in funcs["definitions"] if d.get("is_async")]
    assert {d["type"] for d in async_definitions} == {
        "query",
        "mutation",
        "subscription",
    }


def test_gql_template_adds_funcs_plugin():
    settings = cli_main.build_default_settings("gql")
    funcs = _turms_section(settings)["plugins"][-1]

    assert funcs["type"] == "turms.plugins.funcs.FuncsPlugin"
    assert funcs["global_args"][0]["type"] == "gql.Client"
    assert all("is_async" not in d for d in funcs["definitions"])


def test_strawberry_template_shape():
    settings = cli_main.build_default_settings("strawberry")
    config = yaml.safe_load(settings)
    project = config["projects"]["default"]
    turms = project["extensions"]["turms"]

    assert project["schema"] == "schema.graphql"
    assert "documents" not in project
    assert turms["skip_forwards"] is True
    assert _plugins(settings) == ["turms.plugins.strawberry.StrawberryPlugin"]
    processors = _processors(settings)
    assert processors[0] == "turms.processors.disclaimer.DisclaimerProcessor"
    # libcst is a dev dependency, so merge is scaffolded
    assert "turms.processors.merge.MergeProcessor" in processors


def test_strawberry_template_without_libcst(monkeypatch):
    monkeypatch.setattr(cli_main.importlib.util, "find_spec", lambda name: None)

    processors = _processors(cli_main.build_default_settings("strawberry"))

    assert processors == ["turms.processors.disclaimer.DisclaimerProcessor"]


def test_init_cli_writes_template(tmp_path, monkeypatch):
    """End-to-end: `turms init --template strawberry` writes a parseable config."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli_main.cli, ["init", "--template", "strawberry"])

    assert result.exit_code == 0, result.output
    written = (tmp_path / "graphql.config.yaml").read_text()
    assert _plugins(written) == ["turms.plugins.strawberry.StrawberryPlugin"]


def test_init_cli_rejects_unknown_template(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli_main.cli, ["init", "--template", "nope"])

    assert result.exit_code != 0
    assert not os.path.exists(tmp_path / "graphql.config.yaml")


def test_init_cli_honors_config_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(cli_main.cli, ["init", "--config", ".graphqlrc.yaml"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / ".graphqlrc.yaml").exists()
    assert not (tmp_path / "graphql.config.yaml").exists()
