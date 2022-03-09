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
from turms.processor.base import Processor
from turms.processor.black import BlackProcessor
from turms.registry import ClassRegistry
from turms.stylers import Styler
from turms.utils import build_schema
from turms.plugins.base import Plugin
from turms.compat.funcs import unparse
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


def gen(filepath: str, project=None):

    with open(filepath, "r") as f:
        yaml_dict = yaml.safe_load(f)

    assert "projects" in yaml_dict, "Right now only projects is supported"

    for key, project in yaml_dict["projects"].items():
        try:
            get_console().print(
                f"-------------- Generating project: {key} --------------"
            )
            config = GraphQLConfig(**project, domain=key)

            if isinstance(config.schema_url, AnyHttpUrl):
                schema = build_schema_from_introspect_url(
                    config.schema_url, config.bearer_token
                )
            else:
                schema = build_schema_from_glob(config.schema_url)

            turms_config = project["extensions"]["turms"]

            gen_config = GeneratorConfig(
                **turms_config, documents=project["documents"], domain=config.domain
            )
            plugins = []
            stylers = []
            processors = []

            if "plugins" in turms_config:
                plugin_configs = turms_config["plugins"]
                for plugin_config in plugin_configs:
                    assert (
                        "type" in plugin_config
                    ), "A plugin must at least specify type"
                    plugin_class = import_string(plugin_config["type"])
                    plugins.append(plugin_class(**plugin_config))
                    get_console().print(f"Using Plugin {plugin_class}")

            if "stylers" in turms_config:
                plugin_configs = turms_config["stylers"]
                for plugin_config in plugin_configs:
                    assert (
                        "type" in plugin_config
                    ), "A styler must at least specify type"
                    styler_class = import_string(plugin_config["type"])
                    stylers.append(styler_class(**plugin_config))
                    get_console().print(f"Using Styler {styler_class}")

            if "processors" in turms_config:
                proc_configs = turms_config["processors"]
                for proc_config in proc_configs:
                    assert (
                        "type" in proc_config
                    ), "A processor must at least specify type"
                    proc_class = import_string(proc_config["type"])
                    processors.append(proc_class(**proc_config))
                    get_console().print(f"Using Processor {proc_class}")

            generated_ast = generate_ast(
                gen_config,
                schema,
                plugins=plugins,
                stylers=stylers,
            )

            md = ast.Module(body=generated_ast, type_ignores=[])
            generated = unparse(ast.fix_missing_locations(md))

            for processor in processors:
                generated = processor.run(generated)

            if not os.path.isdir(gen_config.out_dir):
                os.makedirs(gen_config.out_dir)

            with open(
                os.path.join(gen_config.out_dir, gen_config.generated_name), "w"
            ) as f:
                f.write(generated)

            get_console().print("Sucessfull!! :right-facing_fist::left-facing_fist:")
        except:
            get_console().print(
                "-------- ERROR FOR PROJECT: " + key.upper() + " --------"
            )
            get_console().print_exception()
            raise


def generate_ast(
    config: GeneratorConfig,
    schema: GraphQLSchema,
    plugins=plugins,
    stylers=stylers,
):

    global_tree = []
    registry = ClassRegistry(config, stylers)

    for plugin in plugins:
        try:
            global_tree += plugin.generate_ast(schema, config, registry)
        except Exception as e:
            raise GenerationError(f"Plugin:{plugin} failed!") from e

    global_tree = registry.generate_imports() + global_tree

    return global_tree
