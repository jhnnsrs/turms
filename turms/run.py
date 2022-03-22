import ast
import os
from typing import List, Optional

import yaml
from graphql import GraphQLSchema
from pydantic import AnyHttpUrl
from rich import get_console

from turms.config import GeneratorConfig, GraphQLConfig
from turms.helpers import (
    build_schema_from_glob,
    build_schema_from_introspect_url,
    import_string,
)
from turms.plugins.base import Plugin
from turms.processors.base import Processor
from turms.registry import ClassRegistry
from turms.stylers.base import Styler

from .errors import GenerationError


def gen(filepath: Optional[str] = "graphql.config.yaml", project: Optional[str] = None):
    """Generates  Code according to the config file

    Args:
        filepath (str, optional): The filepath of  graphqlconfig. Defaults to "graphql.config.yaml".
        project (str, optional): The project within that should be generated. Defaults to None.
    """

    with open(filepath, "r", encoding="utf-8") as file:
        yaml_dict = yaml.safe_load(file)

    assert "projects" in yaml_dict, "Right now only projects is supported"

    projects = yaml_dict["projects"].items()
    if project:
        projects = [(project, yaml_dict["projects"][project])]

    for key, project in projects:
        try:
            get_console().print(
                f"-------------- Generating project: {key} --------------"
            )
            config = GraphQLConfig(**project, domain=key)

            generated_code = generate(config)

            if not os.path.isdir(config.extensions.turms.out_dir):
                os.makedirs(config.extensions.turms.out_dir)

            with open(
                os.path.join(
                    config.extensions.turms.out_dir,
                    config.extensions.turms.generated_name,
                ),
                "w",
                encoding="utf-8",
            ) as file:
                file.write(generated_code)

            get_console().print("Sucessfull!! :right-facing_fist::left-facing_fist:")
        except:
            get_console().print(
                "-------- ERROR FOR PROJECT: " + key.upper() + " --------"
            )
            get_console().print_exception()
            raise


def instantiate(module_path: str, **kwargs):
    """Instantiate A class from a file.

    Needs to conform to `path.to.module.ClassName`

    Args:
        module_path (str): The class path you would like to instatiate

    Returns:
        object: The instatiated class.
    """
    return import_string(module_path)(**kwargs)


def generate(config: GraphQLConfig) -> str:
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
        config (GraphQLConfig): The configuraion for the generation

    Returns:
        str: The generated code
    """

    if isinstance(config.schema_url, AnyHttpUrl):
        schema = build_schema_from_introspect_url(
            config.schema_url, config.bearer_token
        )
    else:
        schema = build_schema_from_glob(config.schema_url)

    gen_config = config.extensions.turms

    gen_config.documents = config.documents
    gen_config.domain = config.domain
    verbose = gen_config.verbose

    plugins = []
    stylers = []
    parsers = []
    processors = []

    for parser_config in gen_config.parsers:
        x = instantiate(parser_config.type, config=parser_config.dict())
        if verbose:
            get_console().print(f"Using Parser {x}")
        parsers.append(x)

    for plugins_config in gen_config.plugins:
        x = instantiate(plugins_config.type, config=plugins_config.dict())
        if verbose:
            get_console().print(f"Using Plugin {x}")
        plugins.append(x)

    for styler_config in gen_config.stylers:
        x = instantiate(styler_config.type, config=styler_config.dict())
        if verbose:
            get_console().print(f"Using Styler {x}")
        stylers.append(x)

    for proc_config in gen_config.processors:
        x = instantiate(proc_config.type, config=proc_config.dict())
        if verbose:
            get_console().print(f"Using Processor {x}")
        processors.append(x)

    generated_ast = generate_ast(
        gen_config,
        schema,
        plugins=plugins,
        stylers=stylers,
    )

    for parser in parsers:
        generated_ast = parser.parse_ast(generated_ast)

    md = ast.Module(body=generated_ast, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))

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

    global_tree = registry.generate_imports() + global_tree

    return global_tree
