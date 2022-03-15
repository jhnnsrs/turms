import argparse
from enum import Enum
import os
from turms.run import gen
from rich import get_console


directory = os.getcwd()


class TurmsOptions(str, Enum):
    GEN = "gen"
    INIT = "init"
    DOWNLOAD = "download"
    WATCH = "watch"


default_settings = """
projects:
  default:
    schema: https://api.spacex.land/graphql/
    documents: graphql/**.graphql
    extensions:
      turms:
        out_dir: examples/api
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operation.OperationsPlugin
          - type: turms.plugins.funcs.OperationsFuncPlugin
        processors:
          - type: turms.processor.black.BlackProcessor
        scalar_definitions:
          uuid: str
"""


def main(script: TurmsOptions, project=None):

    app_directory = os.getcwd()

    if script == TurmsOptions.INIT:
        get_console().print(f"Creating graphql.config.yaml in {app_directory}")
        with open(os.path.join(app_directory, "graphql.config.yaml"), "w") as f:
            f.write(default_settings)

    if script == TurmsOptions.WATCH:
        from turms.cli.watch import watch

        watch(os.path.join(app_directory, "graphql.config.yaml"), project=project)

    if script == TurmsOptions.GEN:
        gen(os.path.join(app_directory, "graphql.config.yaml"))


def entrypoint():
    parser = argparse.ArgumentParser(description="Say hello")
    parser.add_argument("script", type=TurmsOptions, help="The Script Type")
    parser.add_argument("project", type=str, help="The Path", nargs="?", default=None)
    args = parser.parse_args()
    try:
        main(script=args.script, project=args.project)
    except Exception as e:
        get_console().print_exception()


if __name__ == "__main__":
    entrypoint()
