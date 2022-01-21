from abc import abstractmethod
import ast
from typing import Callable, List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.globals import FRAGMENT_CLASS_MAP, FRAGMENT_DOCUMENT_MAP
from turms.parser.recurse import recurse_annotation
from turms.plugins.base import Plugin
from pydantic import BaseModel
from graphql.language.ast import FragmentDefinitionNode
from turms.utils import (
    NoDocumentsFoundError,
    generate_typename_field,
    parse_documents,
)
import re
from graphql import language, parse, get_introspection_query, validate


from graphql.utilities.type_info import TypeInfo, get_field_def
import logging


logger = logging.getLogger(__name__)


class FragmentsPluginConfig(BaseModel):
    fragment_bases: List[str] = ["turms.types.object.GraphQLObject"]
    fragments_glob: Optional[str]


def generate_fragment(
    f: FragmentDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: FragmentsPluginConfig,
):
    tree = []
    fields = []
    type = client_schema.get_type(f.type_condition.name.value)

    name = f"{config.prepend_fragment}{f.name.value}{config.append_fragment}"

    fields += [generate_typename_field(type.name)]

    for field in f.selection_set.selections:

        field_definition = get_field_def(client_schema, type, field)
        assert field_definition, "Couldn't find field definition"

        target = (
            field.alias.value
            if hasattr(field, "alias") and field.alias
            else field.name.value
        )

        fields.append(
            ast.AnnAssign(
                target=ast.Name(target, ctx=ast.Store()),
                annotation=recurse_annotation(
                    field,
                    field_definition.type,
                    client_schema,
                    config,
                    tree,
                    parent_name=target.capitalize(),
                ),
                simple=1,
            )
        )

    FRAGMENT_DOCUMENT_MAP[f.name.value] = language.print_ast(f)
    FRAGMENT_CLASS_MAP[f.name.value] = name
    tree.append(
        ast.ClassDef(
            name,
            bases=[
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in plugin_config.fragment_bases
            ],
            decorator_list=[],
            keywords=[],
            body=fields,
        )
    )
    return tree


class FragmentsPlugin(Plugin):
    def __init__(self, config=None, **data):
        self.plugin_config = config or FragmentsPluginConfig(**data)

    def generate_imports(
        self, config: GeneratorConfig, client_schema: GraphQLSchema
    ) -> List[ast.AST]:
        imports = []

        all_bases = self.plugin_config.fragment_bases

        for item in all_bases:
            imports.append(
                ast.ImportFrom(
                    module=".".join(item.split(".")[:-1]),
                    names=[ast.alias(name=item.split(".")[-1])],
                    level=0,
                )
            )

        return imports

    def generate_body(
        self, client_schema: GraphQLSchema, config: GeneratorConfig
    ) -> List[ast.AST]:

        plugin_tree = []

        try:
            documents = parse_documents(
                client_schema, self.plugin_config.fragments_glob or config.documents
            )
        except NoDocumentsFoundError as e:
            logger.exception(e)
            return plugin_tree

        definitions = documents.definitions
        fragments = [
            node for node in definitions if isinstance(node, FragmentDefinitionNode)
        ]

        for fragment in fragments:
            plugin_tree += generate_fragment(
                fragment, client_schema, config, self.plugin_config
            )

        return plugin_tree
