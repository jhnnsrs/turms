from abc import abstractmethod
import ast
from typing import Callable, List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.globals import FRAGMENT_CLASS_MAP, FRAGMENT_DOCUMENT_MAP
from turms.parser.recurse import recurse_annotation, type_field_node
from turms.plugins.base import Plugin
from pydantic import BaseModel
from graphql.language.ast import FragmentDefinitionNode
from turms.utils import (
    NoDocumentsFoundError,
    generate_typename_field,
    get_additional_bases_for_type,
    parse_documents,
)
import re
from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLInterfaceType,
    InlineFragmentNode,
    language,
    parse,
    get_introspection_query,
    validate,
)


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

    name = (
        f"{config.prepend_fragment}{f.name.value.capitalize()}{config.append_fragment}"
    )

    if isinstance(type, GraphQLInterfaceType):
        mother_class_fields = []
        base_fragment_name = f"{name}Base"

        if type.description:
            mother_class_fields.append(
                ast.Expr(value=ast.Constant(value=type.description))
            )

        mother_class_fields += [
            ast.AnnAssign(
                target=ast.Name(id="typename", ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name(id="Optional", ctx=ast.Load()),
                    slice=ast.Name("str", ctx=ast.Load()),
                ),
                value=ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(arg="alias", value=ast.Constant(value="__typename"))
                    ],
                ),
                simple=1,
            )
        ]

        for sub_node in f.selection_set.selections:

            if isinstance(sub_node, FieldNode):

                if sub_node.name.value == "__typename":
                    continue

                field_type = type.fields[sub_node.name.value]
                mother_class_fields += type_field_node(
                    sub_node,
                    field_type,
                    client_schema,
                    config,
                    tree,
                    parent_name=base_fragment_name,
                )

        additional_bases = get_additional_bases_for_type(type.name, config)

        mother_class = ast.ClassDef(
            base_fragment_name,
            bases=[
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.interface_bases
            ]
            + additional_bases,  # Todo: fill with base
            decorator_list=[],
            keywords=[],
            body=mother_class_fields if mother_class_fields else [ast.Pass()],
        )

        tree.append(mother_class)

        union_class_names = []

        for sub_node in f.selection_set.selections:

            if isinstance(sub_node, FragmentSpreadNode):

                spreaded_name = f"{base_fragment_name}{sub_node.name.value}"

                cls = ast.ClassDef(
                    spreaded_name,
                    bases=[
                        ast.Name(
                            id=FRAGMENT_CLASS_MAP[sub_node.name.value], ctx=ast.Load()
                        ),
                        ast.Name(id=base_fragment_name, ctx=ast.Load()),
                    ],
                    decorator_list=[],
                    keywords=[],
                    body=[ast.Pass()],
                )

                tree.append(cls)
                union_class_names.append(spreaded_name)

            if isinstance(sub_node, InlineFragmentNode):
                inline_name = (
                    f"{base_fragment_name}{sub_node.type_condition.name.value}Fragment"
                )
                inline_fragment_fields = []

                inline_fragment_fields += [
                    generate_typename_field(sub_node.type_condition.name.value)
                ]

                for sub_sub_node in sub_node.selection_set.selections:

                    if isinstance(sub_sub_node, FieldNode):
                        sub_sub_node_type = client_schema.get_type(
                            sub_node.type_condition.name.value
                        )

                        if sub_sub_node.name.value == "__typename":
                            continue

                        field_type = sub_sub_node_type.fields[sub_sub_node.name.value]
                        inline_fragment_fields += type_field_node(
                            sub_sub_node,
                            field_type,
                            client_schema,
                            config,
                            tree,
                            parent_name=inline_name,
                        )

                additional_bases = get_additional_bases_for_type(
                    sub_node.type_condition.name.value, config
                )
                cls = ast.ClassDef(
                    inline_name,
                    bases=[
                        ast.Name(id=base_fragment_name, ctx=ast.Load()),
                    ],
                    decorator_list=[],
                    keywords=[],
                    body=inline_fragment_fields,
                )

                tree.append(cls)
                union_class_names.append(inline_name)

        union_class_names.append(base_fragment_name)

        FRAGMENT_DOCUMENT_MAP[f.name.value] = language.print_ast(f)
        FRAGMENT_CLASS_MAP[f.name.value] = name

        if len(union_class_names) > 1:
            slice = ast.Tuple(
                elts=[
                    ast.Name(id=clsname, ctx=ast.Load())
                    for clsname in union_class_names
                ],
                ctx=ast.Load(),
            )
            tree.append(
                ast.Assign(
                    targets=[ast.Name(id=name, ctx=ast.Store())],
                    value=ast.Subscript(
                        value=ast.Name("Union", ctx=ast.Load()),
                        slice=slice,
                    ),
                )
            )

        return tree

    name = f"{config.prepend_fragment}{f.name.value}{config.append_fragment}"

    additional_bases = get_additional_bases_for_type(
        f.type_condition.name.value, config
    )

    fields += [generate_typename_field(type.name)]

    for field in f.selection_set.selections:

        if isinstance(field, FragmentDefinitionNode):
            continue

        if isinstance(field, FragmentSpreadNode):
            continue

        field_definition = get_field_def(client_schema, type, field)
        assert field_definition, "Couldn't find field definition"

        target = (
            field.alias.value
            if hasattr(field, "alias") and field.alias
            else field.name.value
        )

        fields += type_field_node(
            field,
            field_definition,
            client_schema,
            config,
            tree,
            parent_name=name,
        )

    FRAGMENT_DOCUMENT_MAP[f.name.value] = language.print_ast(f)
    FRAGMENT_CLASS_MAP[f.name.value] = name
    tree.append(
        ast.ClassDef(
            name,
            bases=additional_bases
            + [
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

        all_bases = {base for base in self.plugin_config.fragment_bases}

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
