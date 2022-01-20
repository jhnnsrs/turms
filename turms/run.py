from graphql import get_introspection_query
from turms.config import GeneratorConfig
from turms.helpers import import_string
from turms.parser.imports import generate_imports
from turms.plugins.structure import StructurePlugin
from turms.processor.base import Processor
from turms.processor.black import BlackProcessor
from turms.utils import build_schema
from turms.plugins.base import Plugin
from typing import Dict, List
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operation import OperationsPlugin
from turms.plugins.funcs import OperationsFuncPlugin
import ast
import yaml
import json
import os
from urllib import request, parse


plugins: List[Plugin] = []

processors: List[Processor] = [
    BlackProcessor(),
]


class GenerationError(Exception):
    pass


def gen(filepath: str):
    with open(filepath, "r") as f:
        settings = yaml.safe_load(f)

    for key, domain in settings.items():
        config = GeneratorConfig(**domain, domain=key)

        if config.schema_url:
            jdata = json.dumps({"query": get_introspection_query()}).encode("utf-8")
            req = request.Request(config.schema_url, data=jdata)
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")

            resp = request.urlopen(req)
            x = json.loads(resp.read().decode("utf-8"))
            introspection = x["data"]
        else:
            raise NotImplementedError("Right now not supported")

        plugins = []

        if "plugins" in domain:
            plugin_configs = domain["plugins"]
            for plugin_config in plugin_configs:
                assert "type" in plugin_config, "A plugin must at least specify type"
                plugin_class = import_string(plugin_config["type"])
                plugins.append(plugin_class(**plugin_config))
                print(f"Using Plugin {plugin_class}")

        processors = []

        if "processors" in domain:
            proc_configs = domain["processors"]
            for proc_config in proc_configs:
                assert "type" in proc_config, "A processor must at least specify type"
                proc_class = import_string(proc_config["type"])
                processors.append(proc_class(**proc_config))
                print(f"Using Processor {proc_class}")

        generate(config, introspection, plugins=plugins, processors=processors)


def generate(
    config: GeneratorConfig,
    introspection_query: Dict[str, str],
    plugins=plugins,
    processors=processors,
):

    client_schema = build_schema(introspection_query)

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
        os.mkdir(config.out_dir)

    with open(os.path.join(config.out_dir, config.generated_name), "w") as f:
        f.write(generated)
