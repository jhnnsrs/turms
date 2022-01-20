from turms.config import GeneratorConfig
from turms.parser.imports import generate_imports
from turms.plugins.structure import StructurePlugin
from turms.processor.base import Processor
from turms.processor.black import BlackProcessor
from turms.utils import build_schema, introspect
from turms.plugins.base import Plugin
from typing import Dict, List
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.operation import OperationsPlugin
from turms.plugins.funcs import OperationsFuncPlugin
import ast

plugins: List[Plugin] = [
    EnumsPlugin(),
    FragmentsPlugin(),
    OperationsPlugin(),
    OperationsFuncPlugin(),
    StructurePlugin(),
]

processors: List[Processor] = [
    BlackProcessor(),
]


class GenerationError(Exception):
    pass


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

    with open(config.generated_name, "w") as f:
        f.write(generated)
