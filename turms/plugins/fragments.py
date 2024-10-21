import ast
from typing import List, Optional

from pydantic_settings import SettingsConfigDict
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.recurse import type_field_node
from turms.plugins.base import Plugin, PluginConfig
from pydantic import Field
from graphql.language.ast import FragmentDefinitionNode
from turms.registry import ClassRegistry
from turms.utils import (
    generate_pydantic_config,
    generate_typename_field,
    get_additional_bases_for_type,
    get_interface_bases,
    parse_documents,
)
from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLInterfaceType,
    GraphQLObjectType,
    InlineFragmentNode,
    language,
)
from turms.config import GraphQLTypes

from graphql.utilities.type_info import get_field_def
import logging


logger = logging.getLogger(__name__)


class FragmentsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PLUGINS_FRAGMENTS_")
    type: str = "turms.plugins.fragments.FragmentsPlugin"
    fragment_bases: List[str] = []
    fragments_glob: Optional[str] = None


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
    name = registry.generate_fragment(
        f.name.value, isinstance(type, GraphQLInterfaceType)
    )

    registry.register_fragment_document(
        f.name.value, language.print_ast(f)
    )  # TODO: Check if typename is being referenced? so that we can check between the elements of the interface

    if isinstance(type, GraphQLInterfaceType):
        mother_class_fields = []
        base_fragment_name = f"{name}"
        additional_bases = get_additional_bases_for_type(type.name, config, registry)

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
                    base_fragment_name,
                    field_type,
                    client_schema,
                    config,
                    tree,
                    registry,
                )

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
                # Spread nodes are like inheritance?
                spreaded_name = f"{base_fragment_name}{sub_node.name.value}"

                cls = ast.ClassDef(
                    spreaded_name,
                    bases=[
                        ast.Name(
                            id=registry.inherit_fragment(sub_node.name.value),
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
                    generate_typename_field(
                        sub_node.type_condition.name.value, registry, config
                    )
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
                            inline_name,
                            field_type,
                            client_schema,
                            config,
                            tree,
                            registry,
                        )

                additional_bases = get_additional_bases_for_type(
                    sub_node.type_condition.name.value, config, registry
                )
                cls = ast.ClassDef(
                    inline_name,
                    bases=[
                        ast.Name(id=base_fragment_name, ctx=ast.Load()),
                    ]
                    + additional_bases,
                    decorator_list=[],
                    keywords=[],
                    body=inline_fragment_fields
                    + generate_pydantic_config(
                        GraphQLTypes.FRAGMENT,
                        config,
                        registry,
                        sub_node.type_condition.name.value,
                    ),
                )

                tree.append(cls)
                union_class_names.append(inline_name)

        union_class_names.append(base_fragment_name)

        if len(union_class_names) > 1:
            registry.register_import("typing.Union")
            slice = ast.Tuple(
                elts=[
                    ast.Name(id=clsname, ctx=ast.Load())
                    for clsname in union_class_names
                ],
                ctx=ast.Load(),
            )
            tree.append(
                ast.Assign(
                    targets=[
                        ast.Name(
                            id=registry.style_fragment_class(f.name.value),
                            ctx=ast.Store(),
                        )
                    ],
                    value=ast.Subscript(
                        value=ast.Name("Union", ctx=ast.Load()),
                        slice=slice,
                        ctx=ast.Load(),
                    ),
                )
            )

        return tree

    elif isinstance(type, GraphQLObjectType):
        additional_bases = get_additional_bases_for_type(
            f.type_condition.name.value, config, registry
        )

        fields += [generate_typename_field(type.name, registry, config)]

        for field in f.selection_set.selections:

            if field.name.value == "__typename":
                continue

            if isinstance(field, FragmentDefinitionNode):  # pragma: no cover

                continue

            if isinstance(field, FragmentSpreadNode):
                additional_bases = [
                    ast.Name(
                        id=registry.inherit_fragment(field.name.value),
                        ctx=ast.Load(),
                    )
                ] + additional_bases  # needs to be prepended (MRO)
                continue

            field_definition = get_field_def(client_schema, type, field)
            assert field_definition, "Couldn't find field definition"

            fields += type_field_node(
                field,
                name,
                field_definition,
                client_schema,
                config,
                tree,
                registry,
            )

        tree.append(
            ast.ClassDef(
                name,
                bases=additional_bases
                + get_fragment_bases(config, plugin_config, registry),
                decorator_list=[],
                keywords=[],
                body=fields
                + generate_pydantic_config(GraphQLTypes.FRAGMENT, config, registry),
            )
        )
        return tree


class FragmentsPlugin(Plugin):
    """Plugin for generating fragments from
    documents

    The fragments plugin will generate classes for each fragment. It loads the documents,
    scans for fragments and generates the classes.

    If encountering a fragment on an interface it will generate a BASE class for that interface
    and then generate a class for each type referenced in the fragment. They will all inherit
    from the base class. The true type will be determined at runtime as all of the potential subtypes
    will be in the same union.

    """

    config: FragmentsPluginConfig = Field(default_factory=FragmentsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        plugin_tree = []

        documents = parse_documents(
            client_schema, self.config.fragments_glob or config.documents
        )

        definitions = documents.definitions

        fragments = [
            node for node in definitions if isinstance(node, FragmentDefinitionNode)
        ]

        for fragment in fragments:
            plugin_tree += generate_fragment(
                fragment, client_schema, config, self.config, registry
            )

        return plugin_tree
