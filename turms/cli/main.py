import argparse
from enum import Enum
import os
from rich.console import Console

directory = os.getcwd()


class TurmsOptions(str, Enum):
    GEN = "gen"
    INIT = "init"
    DOWNLOAD = "download"


default_settings = """
    arkitekt:
        schema: http://localhost:3000/graphql
        out_dir: arkitekt
        plugins: 
            - type: turms.plugins.enums.EnumsPlugin
            - type: turms.plugins.fragments.FragmentsPlugin
              fragment_bases: 
                    - turms.graphql.GraphQLObject

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
        console.log(f"Creating balrd.yaml in {app_directory}")
        with open(os.path.join(app_directory, "baldr.yaml"), "w") as f:
            f.write(default_settings)

    if script.GEN:
        console.log("[red]Error")


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
