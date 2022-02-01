from graphql import get_introspection_query, parse, build_ast_schema
from graphql.language.parser import parse
from pydantic import AnyHttpUrl, NoneIsNotAllowedError
from turms.config import GeneratorConfig, GraphQLConfig
from turms.helpers import import_string
from turms.parser.imports import generate_imports
from turms.processor.base import Processor
from turms.processor.black import BlackProcessor
from turms.utils import build_schema
from turms.plugins.base import Plugin
from turms.compat.funcs import unparse
from typing import Dict, List
import ast
import yaml
import json
import os
from urllib import request
import glob

plugins: List[Plugin] = []

processors: List[Processor] = [
    BlackProcessor(),
]


class GenerationError(Exception):
    pass


def gen(filepath: str, project=None):

    with open(filepath, "r") as f:
        yaml_dict = yaml.safe_load(f)

    assert "projects" in yaml_dict, "Right now only projects is supported"

    for key, project in yaml_dict["projects"].items():
        config = GraphQLConfig(**project, domain=key)

        if isinstance(config.schema_url, AnyHttpUrl):
            jdata = json.dumps({"query": get_introspection_query()}).encode("utf-8")
            req = request.Request(config.schema_url, data=jdata)
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")

            resp = request.urlopen(req)
            x = json.loads(resp.read().decode("utf-8"))
            introspection = x["data"]
            dsl = None
        else:
            schema_glob = glob.glob(config.schema_url, recursive=True)
            dsl_string = ""
            introspection_string = ""
            for file in schema_glob:
                with open(file, "r") as f:
                    if file.endswith(".graphql"):
                        dsl_string += f.read()
                    elif file.endswith(".json"):
                        # not really necessary as json files are generally not splitable
                        introspection_string += f.read

            dsl = parse(dsl_string) if dsl_string is not "" else None
            introspection = (
                json.loads(introspection_string)
                if introspection_string is not ""
                else None
            )

        turms_config = project["extensions"]["turms"]

        gen_config = GeneratorConfig(
            **turms_config, documents=project["documents"], domain=config.domain
        )
        plugins = []

        if "plugins" in turms_config:
            plugin_configs = turms_config["plugins"]
            for plugin_config in plugin_configs:
                assert "type" in plugin_config, "A plugin must at least specify type"
                plugin_class = import_string(plugin_config["type"])
                plugins.append(plugin_class(**plugin_config))
                print(f"Using Plugin {plugin_class}")

        processors = []

        if "processors" in turms_config:
            proc_configs = turms_config["processors"]
            for proc_config in proc_configs:
                assert "type" in proc_config, "A processor must at least specify type"
                proc_class = import_string(proc_config["type"])
                processors.append(proc_class(**proc_config))
                print(f"Using Processor {proc_class}")

        generated_ast = generate_ast(
            gen_config,
            plugins=plugins,
            processors=processors,
            introspection_query=introspection,
            dsl=dsl,
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


def generate_ast(
    config: GeneratorConfig,
    introspection_query: Dict[str, str] = None,
    dsl: any = None,
    plugins=plugins,
    processors=processors,
):
    if introspection_query is not None:
        client_schema = build_schema(introspection_query)
    elif dsl is not None:
        client_schema = build_ast_schema(dsl)
    else:
        raise GenerationError("Either introspection_query or dsl must be provided")

    global_tree = []

    global_tree += generate_imports(client_schema, config)

    for plugin in plugins:
        try:
            global_tree += plugin.generate_imports(client_schema, config)
        except Exception as e:
            raise GenerationError(f"Plugin Imports: {plugin} failed!") from e

    for plugin in plugins:
        try:
            global_tree += plugin.generate_body(client_schema, config)
        except Exception as e:
            raise GenerationError(f"Plugin Body:{plugin} failed!") from e

    return global_tree
