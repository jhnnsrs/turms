import ast
import os
from typing import Dict, List, Optional, Callable, Tuple

import yaml
from graphql import GraphQLSchema, parse, build_ast_schema, build_client_schema, print_ast, print_schema
from pydantic import AnyHttpUrl, ValidationError
from rich import get_console

from turms.config import (
    GeneratorConfig,
    GraphQLConfigMultiple,
    GraphQLConfigSingle,
    GraphQLProject,
    SchemaType,
    LogFunction,
)
from turms.helpers import (
    load_introspection_from_glob,
    load_introspection_from_url,
    load_dsl_from_glob,
    load_dsl_from_url,
    import_string,
)
from turms.plugins.base import Plugin
from turms.parsers.base import Parser
from turms.processors.base import Processor
from turms.registry import ClassRegistry
from turms.stylers.base import Styler
from pydantic import ValidationError

from .errors import GenerationError
import json
import os


try:
    # If toml is installed, use it to load the config file
    import toml

    def toml_loader(file):
        return toml.loads(file.read())

except ImportError:

    def toml_loader(file):
        raise NotImplementedError("TOML not supported. Please install `toml`")


def json_loader(file):
    return json.loads(file.read())


SCANNABLE_FILE_NAMES = [
    "graphql.config.yaml",
    ".graphqlrc.yaml",
    "graphql.config.yml",
    ".graphqlrc.yml",
    "graphql.config.toml",
    ".graphqlrc.toml",
    "graphql.config.json",
    ".graphqlrc.json",
]

FILE_NAME_LOADERS = {
    "yaml": yaml.safe_load,
    "yml": yaml.safe_load,
    "toml": toml_loader,
    "json": json_loader,
}


def get_file_loader(file_name: str) -> Callable:
    try:
        return FILE_NAME_LOADERS[file_name.lower().split(".")[-1]]
    except AttributeError as err:
        raise GenerationError(
            f"File {file_name} is not supported. Please use one of {FILE_NAME_LOADERS.keys()}"
        ) from err


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
        loaded_dict = get_file_loader(config_path)(file)

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
        if file_name.lower() in SCANNABLE_FILE_NAMES
    ]


def scan_folder_for_single_config(folder_path: str = None) -> str:
    """Scans a folder for one single config file

    Args:
        folder_path (str): The path to the folder

    Returns:
        str: The config file
    """

    configs = scan_folder_for_configs(folder_path=folder_path)

    if len(configs) == 0:
        raise GenerationError(
            f"No config files found in {folder_path}. Please use one of {SCANNABLE_FILE_NAMES}. Or use the --config flag to specify a config file."
        )

    if len(configs) != 1:
        raise GenerationError(
            f"Multiple config files found in {folder_path}. Please only have one of {SCANNABLE_FILE_NAMES}. Or use the --config flag to specify a config file."
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


def write_schema_to_file(schema: GraphQLSchema, outdir: str, filepath: str):
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
        file.write(print_schema(schema))

    return generated_file


def write_project(project: GraphQLProject, outdir: str, filepath: str):
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
        file.write(project.model_dump_json(indent=4))

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

            if project.extensions.turms.dump_schema:
                schema = build_schema_from_schema_type(
                            project.schema_url,
                            allow_introspection=project.extensions.turms.allow_introspection,
                        )
                
                write_schema_to_file(schema, project.extensions.turms.out_dir, project.extensions.turms.schema_name)

            if project.extensions.turms.dump_configuration:
                write_project(project, project.extensions.turms.out_dir, project.extensions.turms.configuration_name)






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


def is_url(url: str) -> bool:
    return url.startswith("http") or url.startswith("https")


def build_schema_from_schema_type(
    schema: SchemaType, allow_introspection: bool = False
) -> GraphQLSchema:
    """Builds a schema from a project

    Args:
        project (GraphQLProject): The project

    Returns:
        GraphQLSchema: The schema
    """
    if isinstance(schema, dict):
        if len(schema.values()) == 1:
            key, value = list(schema.items())[0]
            try:
                dsl_string = load_dsl_from_url(key, value.headers)
                return build_ast_schema(parse(dsl_string))
            except Exception as e:
                if allow_introspection:
                    intropection = load_introspection_from_url(key, value.headers)
                    return build_client_schema(intropection)
                raise e
        else:
            # Multiple schemas, now we only support dsl
            dsl_subschemas = []

            for key, value in schema.items():
                dsl_subschemas.append(load_dsl_from_url(key, value.headers))

            return build_ast_schema(parse(" ".join(dsl_subschemas)))

    if isinstance(schema, list):
        if len(schema) == 1:
            # Only one schema, probably because of aesthetic reasons
            return build_schema_from_schema_type(
                schema[0], allow_introspection=allow_introspection
            )

        else:
            dsl_subschemas = []

            for item in schema:
                if is_url(item):
                    dsl_subschemas.append(load_dsl_from_url(item))
                if isinstance(item, dict):
                    for key, value in item.items():
                        dsl_subschemas.append(load_dsl_from_url(key, value.headers))
                if isinstance(item, str):
                    dsl_subschemas.append(load_dsl_from_glob(item))

            return build_ast_schema(parse(" ".join(dsl_subschemas)))

    if is_url(schema):
        try:
            dsl_string = load_dsl_from_url(schema)
            return build_ast_schema(parse(dsl_string))
        except Exception as e:
            if allow_introspection:
                intropection = load_introspection_from_url(schema)
                return build_client_schema(intropection)
            raise e

    if isinstance(schema, str):
        try:
            dsl_string = load_dsl_from_glob(schema)
            return build_ast_schema(parse(dsl_string))
        except Exception as e:
            if allow_introspection:
                intropection = load_introspection_from_glob(schema)
                return build_client_schema(intropection)
            raise e

    raise GenerationError("Could not build schema with type " + str(type(schema)))


def generate(project: GraphQLProject, log: Optional[LogFunction] = None) -> Tuple[str, GraphQLSchema ]:
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
    if not log:

        def log(x, **kwargs):
            return print(x)

    gen_config = project.extensions.turms

    schema = build_schema_from_schema_type(
        project.schema_url,
        allow_introspection=project.extensions.turms.allow_introspection,
    )

    gen_config.documents = gen_config.documents or project.documents
    verbose = gen_config.verbose

    plugins = []
    stylers = []
    parsers = []
    processors = []

    for parser_config in gen_config.parsers:
        styler = instantiate(
            parser_config.type, config=parser_config.model_dump(), log=log
        )
        if verbose:
            get_console().print(f"Using Parser {styler}")
        parsers.append(styler)

    for plugins_config in gen_config.plugins:
        styler = instantiate(
            plugins_config.type, config=plugins_config.model_dump(), log=log
        )
        if verbose:
            get_console().print(f"Using Plugin {styler}")
        plugins.append(styler)

    for styler_config in gen_config.stylers:
        styler = instantiate(
            styler_config.type, config=styler_config.model_dump(), log=log
        )
        if verbose:
            get_console().print(f"Using Styler {styler}")
        stylers.append(styler)

    for proc_config in gen_config.processors:
        styler = instantiate(proc_config.type, config=proc_config.model_dump(), log=log)
        if verbose:
            get_console().print(f"Using Processor {styler}")
        processors.append(styler)

    code = generate_code(
        gen_config,
        schema,
        plugins=plugins,
        stylers=stylers,
        parsers=parsers,
        processors=processors,
        log=log,
    )

    return code, schema


def parse_asts_to_string(generated_ast: List[ast.AST]) -> str:
    module = ast.Module(body=generated_ast, type_ignores=[])
    return ast.unparse(ast.fix_missing_locations(module))


def generate_ast(
    config: GeneratorConfig,
    schema: GraphQLSchema,
    plugins: Optional[List[Plugin]] = None,
    stylers: Optional[List[Styler]] = None,
    skip_forwards: bool = False,
    log: LogFunction = lambda *args, **kwargs: print,
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
    registry = ClassRegistry(config, stylers, log)

    for plugin in plugins:
        try:
            global_tree += plugin.generate_ast(schema, config, registry)
        except Exception as e:
            raise GenerationError(
                f"{plugin.__class__.__name__} failed!\n {str(e)}"
            ) from e

    global_tree = (
        registry.generate_imports() + registry.generate_builtins() + global_tree
    )
    if not skip_forwards:
        global_tree += registry.generate_forward_refs()

    return global_tree


def parse_ast(
    config: GeneratorConfig,
    ast: List[ast.AST],
    parsers: Optional[List[Parser]] = None,
    log: LogFunction = lambda *args, **kwargs: print,
) -> List[ast.AST]:
    """Parses the ast with the plugins

    Args:
        ast (List[ast.AST]): The ast to parse
        plugins (Optional[List[Plugin]], optional): The plugins to use. Defaults to [].
        stylers (Optional[List[Styler]], optional): The plugins to use. Defaults to [].

    Raises:
        GenerationError: Errors involving the generation of the ast

    Returns:
        List[ast.AST]: The parsed ast (as list, not as module)
    """

    parsers = parsers or []

    for parser in parsers:
        try:
            ast = parser.parse_ast(ast)
        except Exception as e:
            raise GenerationError(
                f"{parser.__class__.__name__} failed!\n {str(e)}"
            ) from e

    return ast


def process_code(
    config: GeneratorConfig,
    code: List[ast.AST],
    processors: Optional[List[Processor]] = None,
    log: LogFunction = lambda *args, **kwargs: print,
) -> List[ast.AST]:
    """Parses the ast with the plugins

    Args:
        ast (List[ast.AST]): The ast to parse
        plugins (Optional[List[Plugin]], optional): The plugins to use. Defaults to [].
        stylers (Optional[List[Styler]], optional): The plugins to use. Defaults to [].

    Raises:
        GenerationError: Errors involving the generation of the ast

    Returns:
        List[ast.AST]: The parsed ast (as list, not as module)
    """

    processors = processors or []

    for processor in processors:
        try:
            code = processor.run(code, config)
        except Exception as e:
            raise GenerationError(
                f"{processor.__class__.__name__} failed!\n {str(e)}"
            ) from e

    return code


def generate_code(
    config: GeneratorConfig,
    schema: GraphQLSchema,
    plugins: Optional[List[Plugin]] = None,
    stylers: Optional[List[Styler]] = None,
    parsers: Optional[List[Parser]] = None,
    processors: Optional[List[Processor]] = None,
    log: LogFunction = lambda *args, **kwargs: print,
) -> str:
    generated_ast = generate_ast(
        config,
        schema,
        plugins=plugins,
        stylers=stylers,
        skip_forwards=config.skip_forwards,
        log=log,
    )

    parsed_ast = parse_ast(config, generated_ast, parsers=parsers, log=log)
    code = parse_asts_to_string(parsed_ast)

    processed_code = process_code(config, code, processors=processors, log=log)

    return processed_code
