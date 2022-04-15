import ast
import os
from typing import Dict, List, Optional

import yaml
from graphql import GraphQLSchema
from pydantic import AnyHttpUrl, ValidationError
from rich import get_console

from turms.config import (
    GeneratorConfig,
    GraphQLConfigMultiple,
    GraphQLConfigSingle,
    GraphQLProject,
)
from turms.helpers import (
    build_schema_from_glob,
    build_schema_from_introspect_url,
    import_string,
)
from turms.plugins.base import Plugin
from turms.registry import ClassRegistry
from turms.stylers.base import Styler
from pydantic.error_wrappers import ValidationError

from .errors import GenerationError
import json
import os

try:
    import toml

    def toml_loader(file):
        return toml.loads(file.read())

except ImportError:

    def toml_loader(file):
        raise NotImplementedError("TOML not supported if you dont install `toml`")


def json_loader(file):
    return json.loads(file.read())


FILE_NAME_LOADERS = {
    "graphql.config.yaml": yaml.safe_load,
    ".graphqlrc.yaml": yaml.safe_load,
    "graphql.config.yml": yaml.safe_load,
    ".graphqlrc.yml": yaml.safe_load,
    "graphql.config.toml": toml_loader,
    ".graphqlrc.toml": toml_loader,
    "graphql.config.json": json_loader,
    ".graphqlrc.json": json_loader,
}


def load_projects_from_configpath(
    config_path: str, select: str = None
) -> Dict[str, GraphQLProject]:
    """Loads the configuration from a configuration file

    Args:
        config_path (str): The path to the config file

    Returns:
        GraphQLConfig: The configuration
    """
    file_path, file_name = os.path.split(config_path)

    with open(config_path, "r", encoding="utf-8") as file:

        try:
            loaded_dict = FILE_NAME_LOADERS[file_name.lower()](file)
        except AttributeError as err:
            raise GenerationError(
                f"File {file_name} is not supported. Please use one of {FILE_NAME_LOADERS.keys()}"
            ) from err

    try:
        if "projects" in loaded_dict:
            projects = GraphQLConfigMultiple(**loaded_dict).projects
        else:
            projects = {"default": GraphQLConfigSingle(**loaded_dict)}
    except ValidationError as err:
        raise GenerationError(
            f"File {file_name} at {file_path} does not conform with turms."
        ) from err

    if select:
        projects = {key: project for key, project in projects.items() if key == select}
        assert len(projects) >= 1, "At least one project must be selected"

    return projects


def scan_folder_for_configs(folder_path: str = None) -> List[str]:
    """Scans a folder for config files

    Args:
        folder_path (str): The path to the folder

    Returns:
        List[str]: The list of config files
    """
    if folder_path is None:
        folder_path = os.getcwd()

    return [
        os.path.join(folder_path, file_name)
        for file_name in os.listdir(folder_path)
        if file_name.lower() in FILE_NAME_LOADERS.keys()
    ]


def scan_folder_for_single_config(folder_path: str = None) -> List[str]:
    """Scans a folder for one single config file

    Args:
        folder_path (str): The path to the folder

    Returns:
        str: The config file
    """

    configs = scan_folder_for_configs(folder_path=folder_path)

    if len(configs) == 0:
        raise GenerationError(
            f"No config files found in {folder_path}. Please use one of {FILE_NAME_LOADERS.keys()}"
        )

    if len(configs) != 1:
        raise GenerationError(
            f"Multiple config files found in {folder_path}. Please only have one of {FILE_NAME_LOADERS.keys()}"
        )

    return configs[0]


def write_code_to_file(code: str, outdir: str, filepath: str):

    if not os.path.isdir(outdir):  # pragma: no cover
        os.makedirs(outdir)

    generated_file = os.path.join(
        outdir,
        filepath,
    )

    with open(
        generated_file,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(code)

    return generated_file


def gen(
    filepath: Optional[str] = None,
    project_name: Optional[str] = None,
    strict: bool = False,
    overwrite_path: Optional[str] = None,
):
    """Generates  Code according to the config file

    Args:
        filepath (str, optional): The filepath of  graphqlconfig. Defaults to "graphql.config.yaml".
        project (str, optional): The project within that should be generated. Defaults to None.
    """

    if filepath is None:
        filepath = scan_folder_for_single_config()

    projects = load_projects_from_configpath(filepath, project_name)

    for key, project in projects.items():
        try:
            get_console().print(
                f"-------------- Generating project: {key} --------------"
            )

            generated_code = generate(project)

            write_code_to_file(
                generated_code,
                overwrite_path or project.extensions.turms.out_dir,
                project.extensions.turms.generated_name,
            )

            get_console().print("Sucessfull!! :right-facing_fist::left-facing_fist:")
        except Exception as e:
            get_console().print(
                "-------- ERROR FOR PROJECT: " + key.upper() + " --------"
            )
            get_console().print_exception()
            if strict:
                raise GenerationError from e


def instantiate(module_path: str, **kwargs):
    """Instantiate A class from a file.

    Needs to conform to `path.to.module.ClassName`

    Args:
        module_path (str): The class path you would like to instatiate

    Returns:
        object: The instatiated class.
    """
    return import_string(module_path)(**kwargs)


def generate(project: GraphQLProject) -> str:
    """Genrates the code according to the configugration

    The code is generated in the following order:
        1. Introspect the schema (either url or locally)
        2. Generate the of grapqhl.ast from this schema
        3. Instantiate all plugins/parsers/stylers
        4. Generate the ast from the ast through the plugins and stylers
        5. Parse the Ast with the parsers
        6. Generate the code from the ast through ast.unparse
        7. Process the code string through the processors

    Args:
        project (GraphQLConfig): The configuraion for the generation

    Returns:
        str: The generated code
    """

    if isinstance(project.schema_url, AnyHttpUrl):
        schema = build_schema_from_introspect_url(
            project.schema_url, project.bearer_token
        )
    else:
        schema = build_schema_from_glob(project.schema_url)

    gen_config = project.extensions.turms

    gen_config.documents = gen_config.documents or project.documents
    verbose = gen_config.verbose

    plugins = []
    stylers = []
    parsers = []
    processors = []

    for parser_config in gen_config.parsers:
        styler = instantiate(parser_config.type, config=parser_config.dict())
        if verbose:
            get_console().print(f"Using Parser {styler}")
        parsers.append(styler)

    for plugins_config in gen_config.plugins:
        styler = instantiate(plugins_config.type, config=plugins_config.dict())
        if verbose:
            get_console().print(f"Using Plugin {styler}")
        plugins.append(styler)

    for styler_config in gen_config.stylers:
        styler = instantiate(styler_config.type, config=styler_config.dict())
        if verbose:
            get_console().print(f"Using Styler {styler}")
        stylers.append(styler)

    for proc_config in gen_config.processors:
        styler = instantiate(proc_config.type, config=proc_config.dict())
        if verbose:
            get_console().print(f"Using Processor {styler}")
        processors.append(styler)

    generated_ast = generate_ast(
        gen_config,
        schema,
        plugins=plugins,
        stylers=stylers,
    )

    for styler in parsers:
        generated_ast = styler.parse_ast(generated_ast)

    module = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(module))

    for processor in processors:
        generated = processor.run(generated)

    return generated


def generate_ast(
    config: GeneratorConfig,
    schema: GraphQLSchema,
    plugins: Optional[List[Plugin]] = None,
    stylers: Optional[List[Styler]] = None,
) -> List[ast.AST]:
    """Generates the ast from the schema

    Args:
        config (GeneratorConfig): The generaion Config (turms section)
        schema (GraphQLSchema): The schema to generate the ast from
        plugins (List[Plugins], optional): The plugins to use. Defaults to [].
        stylers (List[Styler], optional): The plugins to use. Defaults to [].

    Raises:
        GenerationError: Errors involving the generation of the ast

    Returns:
        List[ast.AST]: The generated ast (as list, not as module)
    """

    plugins = plugins or []
    stylers = stylers or []

    global_tree = []
    registry = ClassRegistry(config, stylers)

    for plugin in plugins:
        try:
            global_tree += plugin.generate_ast(schema, config, registry)
        except Exception as e:
            raise GenerationError(f"Plugin:{plugin} failed!") from e

    global_tree = (
        registry.generate_imports()
        + registry.generate_builtins()
        + global_tree
        + registry.generate_forward_refs()
    )

    return global_tree
