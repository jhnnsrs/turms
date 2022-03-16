from abc import abstractmethod
import ast
from typing import Callable, List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.recurse import recurse_annotation, type_field_node
from turms.plugins.base import Plugin, PluginConfig
from pydantic import BaseModel, BaseSettings, Field
from graphql.language.ast import FragmentDefinitionNode
from turms.registry import ClassRegistry
from turms.utils import (
    NoDocumentsFoundError,
    generate_config_class,
    generate_typename_field,
    get_additional_bases_for_type,
    get_interface_bases,
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


class FragmentsPluginConfig(PluginConfig):
    type = "turms.plugins.fragments.FragmentsPlugin"
    fragment_bases: List[str] = None
    fragments_glob: Optional[str]

    class Config:
        env_prefix = "TURMS_PLUGINS_FRAGMENTS_"


def get_fragment_bases(
    config: GeneratorConfig,
    pluginConfig: FragmentsPluginConfig,
    registry: ClassRegistry,
):
    if pluginConfig.fragment_bases:
        for base in pluginConfig.fragment_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in pluginConfig.fragment_bases
        ]

    else:
        for base in config.object_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in config.object_bases
        ]


def generate_fragment(
    f: FragmentDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: FragmentsPluginConfig,
    registry: ClassRegistry,
):
    tree = []
    fields = []
    type = client_schema.get_type(f.type_condition.name.value)
    name = registry.generate_fragment_classname(f.name.value)

    if isinstance(type, GraphQLInterfaceType):
        mother_class_fields = []
        base_fragment_name = f"{name}Base"

        if type.description:
            mother_class_fields.append(
                ast.Expr(value=ast.Constant(value=type.description))
            )

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
                    registry,
                    parent_name=base_fragment_name,
                )

        additional_bases = get_additional_bases_for_type(type.name, config, registry)

        mother_class = ast.ClassDef(
            base_fragment_name,
            bases=get_interface_bases(config, registry)
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
                            id=registry.get_fragment_class(sub_node.name.value),
                            ctx=ast.Load(),
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
                    body=inline_fragment_fields + generate_config_class(config),
                )

                tree.append(cls)
                union_class_names.append(inline_name)

        if not config.always_resolve_interfaces:
            union_class_names.append(base_fragment_name)

        registry.register_fragment_document(f.name.value, language.print_ast(f))
        registry.register_fragment_class(f.name.value, name)

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

    name = registry.generate_fragment_classname(f.name.value)

    additional_bases = get_additional_bases_for_type(
        f.type_condition.name.value, config, registry
    )

    fields += [generate_typename_field(type.name, registry)]

    for field in f.selection_set.selections:

        if field.name.value == "__typename":
            continue

        if isinstance(field, FragmentDefinitionNode):
            continue

        if isinstance(field, FragmentSpreadNode):
            continue

        field_definition = get_field_def(client_schema, type, field)
        assert field_definition, "Couldn't find field definition"

        fields += type_field_node(
            field,
            field_definition,
            client_schema,
            config,
            tree,
            registry,
            parent_name=name,
        )

    registry.register_fragment_document(f.name.value, language.print_ast(f))
    registry.register_fragment_class(f.name.value, name)
    tree.append(
        ast.ClassDef(
            name,
            bases=additional_bases
            + get_fragment_bases(config, plugin_config, registry),
            decorator_list=[],
            keywords=[],
            body=fields + generate_config_class(config),
        )
    )
    return tree


class FragmentsPlugin(Plugin):
    config: FragmentsPluginConfig = Field(default_factory=FragmentsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        plugin_tree = []

        try:
            documents = parse_documents(
                client_schema, self.config.fragments_glob or config.documents
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
                fragment, client_schema, config, self.config, registry
            )

        return plugin_tree
