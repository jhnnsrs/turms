from click.testing import CliRunner
from turms.cli.main import cli
import shutil
from .utils import build_relative_glob
import os


def test_run_gen(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli.yaml")
    d = build_relative_glob("/documents/countries")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        shutil.copytree(d, os.path.join(td, "graphql"))

        result = runner.invoke(cli, ["gen"])
        assert result.exit_code == 0


def test_run_gen_multiple(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli_multi_projects.yaml")
    country_documents = build_relative_glob("/documents/countries")
    nested_input_documents = build_relative_glob("/documents/nested_inputs")
    nested_schema = build_relative_glob("/schemas/nested_inputs.graphql")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        schema_dir = os.path.join(td, "schema")
        graphql_dir = os.path.join(td, "graphql")
        os.mkdir(schema_dir)
        os.mkdir(graphql_dir)

        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        shutil.copyfile(
            nested_schema, os.path.join(schema_dir, "nested_inputs.graphql")
        )
        shutil.copytree(country_documents, os.path.join(graphql_dir, "countries"))
        shutil.copytree(
            nested_input_documents, os.path.join(graphql_dir, "nested_inputs")
        )

        result = runner.invoke(cli, ["gen"])
        assert result.exit_code == 0


def test_run_gen_display_errors(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli_multi_projects.yaml")
    country_documents = build_relative_glob("/documents/countries")
    # nested_input_documents = build_relative_glob("/documents/nested_inputs")
    # This test is to ensure that the cli will display errors when documents are missing
    nested_schema = build_relative_glob("/schemas/nested_inputs.graphql")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        schema_dir = os.path.join(td, "schema")
        graphql_dir = os.path.join(td, "graphql")
        os.mkdir(schema_dir)
        os.mkdir(graphql_dir)

        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        shutil.copyfile(
            nested_schema, os.path.join(schema_dir, "nested_inputs.graphql")
        )
        shutil.copytree(country_documents, os.path.join(graphql_dir, "countries"))

        result = runner.invoke(cli, ["gen"])
        assert result.exit_code == 1
        assert "*.graphql" in result.output


def test_run_gen_multiple_but_one(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli_multi_projects.yaml")
    country_documents = build_relative_glob("/documents/countries")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        schema_dir = os.path.join(td, "schema")
        graphql_dir = os.path.join(td, "graphql")
        os.mkdir(schema_dir)
        os.mkdir(graphql_dir)

        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        shutil.copytree(country_documents, os.path.join(graphql_dir, "countries"))

        result = runner.invoke(cli, ["gen", "countries"])
        assert result.exit_code == 0


def test_run_download(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli.yaml")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        result = runner.invoke(cli, ["download"])

        assert os.path.exists(os.path.join(td, "default.schema.graphql"))
        assert result.exit_code == 0


def test_run_download_multiple(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli_multi_projects.yaml")
    nested_schema = build_relative_glob("/schemas/nested_inputs.graphql")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        schema_dir = os.path.join(td, "schema")
        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        os.mkdir(schema_dir)

        shutil.copyfile(
            nested_schema, os.path.join(schema_dir, "nested_inputs.graphql")
        )

        result = runner.invoke(cli, ["download"])
        assert result.exit_code == 0
        assert os.path.exists(
            os.path.join(td, "countries.schema.graphql")
        ), "countries schema not found"
        assert os.path.exists(
            os.path.join(td, "nested_inputs.schema.graphql")
        ), "nested_inputs schema not found"


def test_run_init(tmp_path):
    runner = CliRunner()

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        result = runner.invoke(cli, ["init"])

        assert os.path.exists(os.path.join(td, "graphql.config.yaml"))
        assert result.exit_code == 0


def test_run_init(tmp_path):
    runner = CliRunner()

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        result = runner.invoke(cli, ["init"])

        assert os.path.exists(os.path.join(td, "graphql.config.yaml"))
        assert result.exit_code == 0


def test_run_error_code(tmp_path):
    runner = CliRunner()

    c = build_relative_glob("/configs/test_cli.yaml")
    d = build_relative_glob("/documents/error_documents")

    # Move config file to temp dir

    with runner.isolated_filesystem(temp_dir=tmp_path) as td:

        shutil.copyfile(c, os.path.join(td, "graphql.config.yaml"))
        shutil.copytree(d, os.path.join(td, "graphql"))

        result = runner.invoke(cli, ["gen"])
        assert result.exit_code == 1
