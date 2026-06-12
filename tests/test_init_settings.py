import yaml

from turms.cli import main as cli_main


def _processors(settings: str):
    config = yaml.safe_load(settings)
    turms = config["projects"]["default"]["extensions"]["turms"]
    return [p["type"] for p in turms.get("processors", [])]


def test_default_settings_include_installed_formatters():
    """black and isort are dev dependencies, so the scaffold includes both."""
    processors = _processors(cli_main.build_default_settings())

    assert "turms.processors.black.BlackProcessor" in processors
    assert "turms.processors.isort.IsortProcessor" in processors


def test_default_settings_skip_missing_formatters(monkeypatch):
    """Without black/isort installed, no processors section is scaffolded."""
    monkeypatch.setattr(
        cli_main.importlib.util, "find_spec", lambda name: None
    )

    settings = cli_main.build_default_settings()

    assert _processors(settings) == []
    assert "processors" not in settings


def test_default_settings_partial_install(monkeypatch):
    """Only the processor whose tool is installed is scaffolded."""
    monkeypatch.setattr(
        cli_main.importlib.util,
        "find_spec",
        lambda name: object() if name == "black" else None,
    )

    processors = _processors(cli_main.build_default_settings())

    assert processors == ["turms.processors.black.BlackProcessor"]


def test_default_settings_are_valid_yaml_with_plugins():
    """The scaffold parses as YAML and always carries the core plugins."""
    config = yaml.safe_load(cli_main.build_default_settings())
    turms = config["projects"]["default"]["extensions"]["turms"]
    plugin_types = [p["type"] for p in turms["plugins"]]

    assert "turms.plugins.operations.OperationsPlugin" in plugin_types
    assert turms["scalar_definitions"] == {"uuid": "str"}
