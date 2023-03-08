import argparse
from enum import Enum
import os
from turms.run import gen
from rich import get_console
from rich.prompt import Prompt
from rich.panel import Panel
import rich_click as click
from turms.run import (
    scan_folder_for_single_config,
    load_projects_from_configpath,
    build_schema_from_schema_type,
)
from graphql import print_schema

click.rich_click.USE_RICH_MARKUP = True

directory = os.getcwd()


class TurmsOptions(str, Enum):
    GEN = "gen"
    INIT = "init"
    DOWNLOAD = "download"
    WATCH = "watch"


logo = """
   __                           
  / /___  ___________ ___  _____
 / __/ / / / ___/ __ `__ \/ ___/
/ /_/ /_/ / /  / / / / / (__  ) 
\__/\__,_/_/  /_/ /_/ /_/____/  
"""

welcome = """
Welcome to Turms! Turms is a GraphQL code generator that generates code from your GraphQL schema and documents. For more information, visit
https://gihub.com/jhnnsrs/turms
"""

default_settings = """
projects:
  default:
    schema: https://countries.trevorblades.com/
    documents: graphql/**.graphql
    extensions:
      turms:
        out_dir: examples/api
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
          - type: turms.plugins.funcs.FuncsPlugin
        processors:
          - type: turms.processors.black.BlackProcessor
        scalar_definitions:
          uuid: str
"""


@click.group()
def cli():
    """Welcome to turms!

    Welcome to Turms! Turms is a GraphQL code generator that generates code from your GraphQL schema and documents.

    For more information, visit [link=https://gihub.com/jhnnsrs/turms] https://gihub.com/jhnnsrs/turms [/link]"""
    pass


@cli.command()
def init():

    get_console().print(f"Creating graphql.config.yaml in {app_directory}")
    with open(os.path.join(app_directory, "graphql.config.yaml"), "w") as f:
        f.write(default_settings)


@cli.command()
@click.option("--config", default=None)
@click.option("--project", default=None)
@click.option("--schema", default=None)
@click.option("--documents", default=None)
@click.option("--out", default=None)
@click.option("--plugins", default=None)
def gen(project, schema, documents, out, plugins):
    """Generate the graphql project"""


@cli.command()
def watch():
    """Watch the graphql project"""
    raise Exception("No longer supported")


@cli.command()
@click.option("--project", default=None)
@click.option("--out", default=".schema.graphql")
def download(project, out):
    """Download the graphql projects schema as a sdl file"""
    app_directory = os.getcwd()
    config = scan_folder_for_single_config(app_directory)
    projects = load_projects_from_configpath(config)
    if project:
        projects = {key: value for key, value in projects if key == project}

    for key, project in projects.items():
        filename = f"{key}{out}"
        get_console().print(f"Downloading schema for project {key} to {filename}")
        schema = build_schema_from_schema_type(
            project.schema_url, allow_introspection=True
        )
        with open(os.path.join(app_directory, filename), "w") as f:
            f.write(print_schema(schema))


if __name__ == "__main__":
    cli()
