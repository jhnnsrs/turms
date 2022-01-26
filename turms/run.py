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
from typing import Dict, List
import ast
import yaml
import json
import os
from urllib import request


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
            with open(os.path.join(os.getcwd(), config.schema_url), "r") as f:
                if config.schema_url.endswith(".graphql"):
                    dsl = parse(f.read())
                    introspection = None
                elif config.schema_url.endswith(".json"):
                    introspection = json.load(f)
                    dsl = None

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

        generate(
            gen_config,
            plugins=plugins,
            processors=processors,
            introspection_query=introspection,
            dsl=dsl,
        )


def generate(
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

    md = ast.Module(body=global_tree, type_ignores=[])
    generated = ast.unparse(ast.fix_missing_locations(md))

    for processor in processors:
        generated = processor.run(generated)

    if not os.path.isdir(config.out_dir):
        os.makedirs(config.out_dir)

    with open(os.path.join(config.out_dir, config.generated_name), "w") as f:
        f.write(generated)
