import argparse
from enum import Enum
import os
from rich.console import Console

from turms.run import gen

directory = os.getcwd()


class TurmsOptions(str, Enum):
    GEN = "gen"
    INIT = "init"
    DOWNLOAD = "download"


default_settings = """
default:
  schema_url: https://api.spacex.land/graphql/
  plugins:
    - type: turms.plugins.enums.EnumsPlugin
    - type: turms.plugins.fragments.FragmentsPlugin
      fragments_glob: graphql/**.graphql
    - type: turms.plugins.operation.OperationsPlugin
      operations_glob: graphql/**.graphql
    - type: turms.plugins.funcs.OperationsFuncPlugin
      funcs_glob: graphql/**.graphql
  processors:
    - type: turms.processor.black.BlackProcessor
"""


def main(script: TurmsOptions, path: str):
    console = Console()

    if path == ".":
        app_directory = os.getcwd()
        name = os.path.basename(app_directory)
    else:
        app_directory = os.path.join(os.getcwd(), path)
        name = path

    if script.INIT:
        console.log(f"Creating turms.yaml in {app_directory}")
        with open(os.path.join(app_directory, "turms.yaml"), "w") as f:
            f.write(default_settings)

    if script.GEN:
        gen(os.path.join(app_directory, "turms.yaml"))


def entrypoint():
    parser = argparse.ArgumentParser(description="Say hello")
    parser.add_argument("script", type=TurmsOptions, help="The Script Type")
    parser.add_argument("path", type=str, help="The Path", nargs="?", default=".")
    parser.add_argument(
        "--services",
        type=str,
        help="The services you want to connect to (seperated by ,)",
    )
    args = parser.parse_args()

    main(
        script=args.script,
        path=args.path,
    )


if __name__ == "__main__":
    entrypoint()
