from graphql import GraphQLSchema, get_introspection_query, parse, build_ast_schema
from graphql.language.parser import parse
from pydantic import AnyHttpUrl, NoneIsNotAllowedError
from rich import get_console
from turms.config import GeneratorConfig, GraphQLConfig
from turms.helpers import (
    build_schema_from_glob,
    build_schema_from_introspect_url,
    import_string,
)
from turms.processors.base import Processor
from turms.processors.black import BlackProcessor
from turms.registry import ClassRegistry
from turms.stylers import Styler
from turms.stylers.default import DefaultStyler
from turms.utils import build_schema
from turms.plugins.base import Plugin
from typing import Dict, List
import ast
import yaml
import json
import os
from urllib import request
from urllib.error import URLError
import glob
from .errors import GenerationError

plugins: List[Plugin] = []
processors: List[Processor] = []
stylers: List[Styler] = []


def gen(filepath: str = "graphql.config.yaml", project=None):

    with open(filepath, "r") as f:
        yaml_dict = yaml.safe_load(f)

    assert "projects" in yaml_dict, "Right now only projects is supported"

    for key, project in yaml_dict["projects"].items():
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
            ) as f:
                f.write(generated_code)

            get_console().print("Sucessfull!! :right-facing_fist::left-facing_fist:")
        except:
            get_console().print(
                "-------- ERROR FOR PROJECT: " + key.upper() + " --------"
            )
            get_console().print_exception()
            raise


def instantiate(filepath: str, **kwargs):
    return import_string(filepath)(**kwargs)


def generate(config: GraphQLConfig) -> str:

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
    plugins=plugins,
    stylers=stylers,
) -> List[ast.AST]:

    global_tree = []
    registry = ClassRegistry(config, stylers)

    for plugin in plugins:
        try:
            global_tree += plugin.generate_ast(schema, config, registry)
        except Exception as e:
            raise GenerationError(f"Plugin:{plugin} failed!") from e

    global_tree = registry.generate_imports() + global_tree

    return global_tree
