from enum import Enum
import importlib.util
import os
from typing import Any, Callable, Dict

import yaml
from turms.config import GraphQLProject
from turms.run import generate, write_code_to_file, write_project, write_schema_to_file
from rich import get_console
from rich.panel import Panel
from rich.live import Live
from rich.tree import Tree
from rich.console import Group
import rich_click as click
from turms.run import (
    scan_folder_for_single_config,
    load_projects_from_configpath,
    build_schema_from_schema_type,
)
from .watch import stream_changes
from graphql import print_schema
from functools import wraps

click.rich_click.USE_RICH_MARKUP = True

directory = os.getcwd()


class TurmsOptions(str, Enum):
    GEN = "gen"
    INIT = "init"
    DOWNLOAD = "download"
    WATCH = "watch"


logo = r"""
   __                             
  / /___  ___________ ___  _____
 / __/ / / / ___/ __ `__ \/ ___/
/ /_/ /_/ / /  / / / / / (__  ) 
\__/\__,_/_/  /_/ /_/ /_/____/  
"""

welcome = """
Welcome to Turms! Turms is a GraphQL code generator that generates code from your GraphQL schema and documents. For more information, visit
https://github.com/jhnnsrs/turms
"""


optional_processors = {
    "black": "turms.processors.black.BlackProcessor",
    "isort": "turms.processors.isort.IsortProcessor",
}

DEFAULT_STYLERS = [
    {"type": "turms.stylers.capitalize.CapitalizeStyler"},
    {"type": "turms.stylers.snake_case.SnakeCaseStyler"},
]

DOCUMENT_PLUGINS = [
    {"type": "turms.plugins.enums.EnumsPlugin"},
    {"type": "turms.plugins.inputs.InputsPlugin"},
    {"type": "turms.plugins.fragments.FragmentsPlugin"},
    {"type": "turms.plugins.operations.OperationsPlugin"},
]


def detected_formatter_processors() -> list[dict]:
    """Processors for the formatters (black, isort) that are installed in the
    current environment."""
    return [
        {"type": processor}
        for module, processor in optional_processors.items()
        if importlib.util.find_spec(module) is not None
    ]


def _project(turms: dict, schema: str, documents: str | None) -> dict:
    project: dict = {"schema": schema}
    if documents:
        project["documents"] = documents
    project["extensions"] = {"turms": turms}
    return {"projects": {"default": project}}


def build_documents_template() -> dict:
    """Pydantic models (enums, inputs, fragments, operations) from documents."""
    turms: dict = {
        "out_dir": "api",
        "stylers": DEFAULT_STYLERS,
        "plugins": DOCUMENT_PLUGINS,
    }
    processors = detected_formatter_processors()
    if processors:
        turms["processors"] = processors
    turms["scalar_definitions"] = {"uuid": "str"}
    return _project(turms, "https://countries.trevorblades.com/", "graphql/**.graphql")


def build_rath_template() -> dict:
    """Documents template plus typed call functions for the rath client."""
    settings = build_documents_template()
    turms = settings["projects"]["default"]["extensions"]["turms"]
    turms["plugins"] = DOCUMENT_PLUGINS + [
        {
            "type": "turms.plugins.funcs.FuncsPlugin",
            "global_kwargs": [
                {
                    "type": "rath.Rath",
                    "key": "rath",
                    "description": "The client we want to use (defaults to the currently active client)",
                }
            ],
            "definitions": [
                {"type": "query", "is_async": True, "use": "api.proxies.aexecute"},
                {"type": "mutation", "is_async": True, "use": "api.proxies.aexecute"},
                {
                    "type": "subscription",
                    "is_async": True,
                    "use": "api.proxies.asubscribe",
                },
                {"type": "query", "use": "api.proxies.execute"},
                {"type": "mutation", "use": "api.proxies.execute"},
                {"type": "subscription", "use": "api.proxies.subscribe"},
            ],
        }
    ]
    return settings


def build_gql_template() -> dict:
    """Documents template plus typed call functions for the gql client."""
    settings = build_documents_template()
    turms = settings["projects"]["default"]["extensions"]["turms"]
    turms["plugins"] = DOCUMENT_PLUGINS + [
        {
            "type": "turms.plugins.funcs.FuncsPlugin",
            "global_args": [
                {
                    "type": "gql.Client",
                    "key": "client",
                    "description": "The client we want to use to execute the operation",
                }
            ],
            "definitions": [
                {"type": "query", "use": "api.proxies.execute"},
                {"type": "mutation", "use": "api.proxies.execute"},
                {"type": "subscription", "use": "api.proxies.subscribe"},
            ],
        }
    ]
    return settings


def build_strawberry_template() -> dict:
    """Server-side strawberry schema scaffold from a local SDL file."""
    processors = [{"type": "turms.processors.disclaimer.DisclaimerProcessor"}]
    processors += detected_formatter_processors()
    if importlib.util.find_spec("libcst") is not None:
        processors.append({"type": "turms.processors.merge.MergeProcessor"})
    turms = {
        "out_dir": "api",
        "skip_forwards": True,
        "stylers": DEFAULT_STYLERS,
        "plugins": [{"type": "turms.plugins.strawberry.StrawberryPlugin"}],
        "processors": processors,
        "scalar_definitions": {"uuid": "str"},
    }
    return _project(turms, "schema.graphql", None)


TEMPLATES: Dict[str, dict] = {
    "documents": {
        "build": build_documents_template,
        "hint": "Write your operations in [b]graphql/*.graphql[/b] and run [b]turms gen[/b].",
    },
    "rath": {
        "build": build_rath_template,
        "hint": "This template generates typed call functions for [b]rath[/b]: install rath and create an [b]api/proxies.py[/b] with execute/aexecute/subscribe/asubscribe (see examples/rath-usage).",
    },
    "gql": {
        "build": build_gql_template,
        "hint": "This template generates typed call functions for [b]gql[/b]: install gql and create an [b]api/proxies.py[/b] with execute/subscribe (see examples/gql-usage).",
    },
    "strawberry": {
        "build": build_strawberry_template,
        "hint": "Point [b]schema:[/b] at your SDL file (schema.graphql) and run [b]turms gen[/b] to scaffold a strawberry server.",
    },
}


def build_default_settings(template: str = "documents") -> str:
    """Render the named template (documents, rath, gql, strawberry) to YAML,
    adapted to the tools installed in the current environment."""
    return yaml.dump(
        TEMPLATES[template]["build"](), sort_keys=False, default_flow_style=False
    )


def generate_projects(projects: Dict[str, GraphQLProject], title: str = "Turms"):
    generation_message = f"Generating the {'.'.join(projects.keys())} projects. This may take a while...\n"

    tree = Tree("Generating projects", style="bold green")
    panel_group = Group(generation_message, tree)

    panel = Panel(
        panel_group,
        title=title,
        title_align="left",
        border_style="green",
        padding=(1, 1),
    )

    raised_exceptions: list[Exception] = []

    with Live(panel, screen=False) as live:
        for key, project in projects.items():
            project_tree = Tree(f"{key}", style="not bold white")
            tree.add(project_tree)
            live.update(panel)

            def log(message: str, level: str = "INFO"):
                if level == "WARN":
                    project_tree.add(Tree(message, style="yellow"))

            try:
                generated_code, schema = generate(project, log=log)

                project_tree.label = f"{key} ✔️"
                live.update(panel)

                write_code_to_file(
                    generated_code,
                    project.extensions.turms.out_dir,
                    project.extensions.turms.generated_name,
                )

                if project.extensions.turms.dump_schema:
                    write_schema_to_file(
                        schema,
                        project.extensions.turms.out_dir,
                        project.extensions.turms.schema_name,
                    )

                if project.extensions.turms.dump_configuration:
                    write_project(
                        project,
                        project.extensions.turms.out_dir,
                        project.extensions.turms.configuration_name,
                    )

            except Exception as e:
                project_tree.style = "red"
                project_tree.label = f"{key} 💥"
                project_tree.add(Tree(str(e), style="red"))
                if project.extensions.turms.exit_on_error:
                    raised_exceptions.append(e)
                live.update(panel)

    if raised_exceptions:
        # print traceback of first exception
        for e in raised_exceptions:
            try:
                raise e
            except Exception:
                get_console().print_exception()

        raise click.ClickException(
            "One or more projects failed to generate. First error"
        ) from raised_exceptions[0]


def with_projects(
    func: Callable[[click.Context], None],
) -> Callable[[click.Context], None]:
    @click.argument("project", default=None, required=False)
    @click.option("--config", default=None)
    @wraps(func)
    def wrapper(
        *args: Any, config: str | None = None, project: str | None = None, **kwargs: Any
    ):
        try:
            app_directory = os.getcwd()
            config = config or scan_folder_for_single_config(app_directory)
            if not config:
                raise Exception(
                    f"No config file found. Please run `turms init` in {app_directory} to create a default config file or specify a config file with the --config flag"
                )

            try:
                projects = load_projects_from_configpath(config)
            except Exception as e:
                get_console().print_exception()
                raise e

            if project:
                projects = {
                    key: value for key, value in projects.items() if key == project
                }
                if not projects:
                    raise Exception(f"Project {project} not found in {config}")

        except Exception as e:
            raise click.ClickException(str(e)) from e

        return func(*args, projects=projects, **kwargs)

    return wrapper


def watch_projects(projects, title="Turms"):  # pragma: no cover
    if len(projects) > 1:
        raise click.ClickException(
            "Watching multiple projects is not supported. Please specify a single project!"
        )

    project = list(projects.values())[0]

    generation_message = f"Watching the {'.'.join(projects.keys())} project. Changes will be automatically generated and added to [b]{project.extensions.turms.out_dir}/{project.extensions.turms.generated_name}[/b] when you save a file in the project's documents folder."

    tree = Panel("Watching....", style="bold green")
    panel_group = Group(generation_message, tree)

    panel = Panel(
        panel_group,
        title=title,
        title_align="left",
        border_style="green",
        padding=(1, 1),
    )

    with Live(panel, screen=False) as live:
        tree.renderable = f"Watching {project.documents}..."
        live.update(panel)

        for event in stream_changes(project.documents):
            live.update(panel)

            try:
                tree.renderable = "Generating..."
                tree.border_style = "blue"
                tree.style = "blue"
                live.update(panel)

                generated_code, schema = generate(
                    project,
                )

                write_code_to_file(
                    generated_code,
                    project.extensions.turms.out_dir,
                    project.extensions.turms.generated_name,
                )

                tree.renderable = "Generation Successfull"
                tree.border_style = "green"
                tree.style = "green"
                live.update(panel)

            except Exception as e:
                tree.renderable = f"[red] {str(e)} [/],"
                tree.border_style = "not bold red"
                tree.style = "not bold red"
                live.update(panel)
                continue


@click.group()
@click.pass_context
def cli(ctx):
    """Welcome to turms!

    Welcome to Turms! Turms is a GraphQL code generator that generates code from your GraphQL schema and documents.

    For more information, visit [link=https://github.com/jhnnsrs/turms] https://github.com/jhnnsrs/turms [/link]
    """


@cli.command()
@click.option("--config", default="graphql.config.yaml", help="The config file to use")
@click.option(
    "--template",
    type=click.Choice(list(TEMPLATES)),
    default="documents",
    show_default=True,
    help="The starter template to scaffold: pydantic models from documents, "
    "documents plus call functions for rath or gql, or a strawberry server schema",
)
def init(config, template):
    """Initialize a new graphql project"""
    welcome_panel = Panel(logo + welcome, title="turms", border_style="bold green")

    get_console().print(welcome_panel)

    app_directory = os.getcwd()
    if os.path.exists(os.path.join(app_directory, config)):
        if not click.confirm(
            f"Config file already exists in {app_directory}. Do you want to overwrite it?",
            default=False,
        ):
            get_console().print("Aborting")
            return

    get_console().print(
        f"Creating {config} in {app_directory} (template: {template})"
    )
    with open(os.path.join(app_directory, config), "w") as f:
        f.write(build_default_settings(template))

    get_console().print(TEMPLATES[template]["hint"])


@cli.command()
@with_projects
def gen(projects):
    """Generate the graphql project"""
    generate_projects(projects)


@cli.command()
@with_projects
def watch(projects):  # pragma: no cover
    """Watch the graphql project"""
    watch_projects(projects)


@cli.command()
@with_projects
@click.option(
    "--out",
    default=".schema.graphql",
    help="The output file extension (will be appended to the project name)",
)
@click.option(
    "--dir",
    default=None,
    help="The output directory for the schema files (will default to the current working directory)",
)
def download(projects, out, dir):
    """Download the graphql projects schema as a sdl file"""

    try:
        app_directory = dir or os.getcwd()
        for key, project in projects.items():
            filename = f"{key}{out}"
            get_console().print(
                f"Downloading schema for project {key} to {app_directory}/{filename}"
            )
            schema = build_schema_from_schema_type(
                project.schema_url, allow_introspection=True
            )
            with open(os.path.join(app_directory, filename), "w") as f:
                f.write(print_schema(schema))
    except Exception as e:
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    cli()
