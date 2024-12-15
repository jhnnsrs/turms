import ast
import logging
from collections import defaultdict, deque
from typing import List, Optional

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLUnionType,
    InlineFragmentNode,
    SelectionSetNode,
    language,
)
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.utilities.type_info import get_field_def
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from turms.config import GeneratorConfig, GraphQLTypes
from turms.plugins.base import Plugin, PluginConfig
from turms.recurse import type_field_node
from turms.registry import ClassRegistry
from turms.utils import (
    generate_generic_typename_field,
    generate_pydantic_config,
    generate_typename_field,
    get_additional_bases_for_type,
    get_interface_bases,
    non_typename_fields,
    parse_documents,
)

logger = logging.getLogger(__name__)


def find_fragment_dependencies_recursive(selection_set: SelectionSetNode, fragment_definitions, visited):
    """Recursively find all fragment dependencies within a selection set."""
    dependencies = set()
    if selection_set is None:
        return dependencies

    for selection in selection_set.selections:
        # If we encounter a fragment spread, add it to dependencies
        if isinstance(selection, FragmentSpreadNode):
            spread_name = selection.name.value
            dependencies.add(spread_name)
            # Recursively add dependencies of the spread fragment
            if spread_name in fragment_definitions and spread_name not in visited:
                visited.add(spread_name)  # Prevent cycles in recursion
                fragment = fragment_definitions[spread_name]
                dependencies.update(
                    find_fragment_dependencies_recursive(fragment.selection_set, fragment_definitions, visited)
                )
        # If it's a field with a nested selection set, dive deeper
        elif isinstance(selection, FieldNode) and selection.selection_set:
            dependencies.update(
                find_fragment_dependencies_recursive(selection.selection_set, fragment_definitions, visited)
            )


    return dependencies

def build_recursive_dependency_graph(document):
    """Build a dependency graph for fragments, accounting for deep nested fragment spreads."""
    fragment_definitions = {
        definition.name.value: definition for definition in document.definitions
        if isinstance(definition, FragmentDefinitionNode)
    }
    dependencies = defaultdict(set)
    
    # Populate the dependency graph with deeply nested fragment dependencies
    for fragment_name, fragment in fragment_definitions.items():
        visited = set()  # Track visited fragments to avoid cyclic dependencies
        dependencies[fragment_name] = find_fragment_dependencies_recursive(fragment.selection_set, fragment_definitions, visited)
    
    return dependencies


def topological_sort(dependency_graph):
    """Perform a topological sort on fragments based on recursive dependencies."""
    sorted_fragments = []
    no_dependency_fragments = deque([frag for frag, deps in dependency_graph.items() if not deps])
    resolved = set(no_dependency_fragments)
    
    while no_dependency_fragments:
        fragment = no_dependency_fragments.popleft()
        sorted_fragments.append(fragment)
        
        # Remove this fragment from other fragments' dependencies
        for frag, deps in dependency_graph.items():
            if fragment in deps:
                deps.remove(fragment)
                if not deps and frag not in resolved:
                    no_dependency_fragments.append(frag)
                    resolved.add(frag)
    
    # Add any remaining fragments that may have been missed if they were independent
    sorted_fragments.extend(frag for frag in dependency_graph if frag not in sorted_fragments)
    
    return sorted_fragments


class FragmentsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PLUGINS_FRAGMENTS_")
    type: str = "turms.plugins.fragments.FragmentsPlugin"
    fragment_bases: List[str] = []
    fragments_glob: Optional[str] = None
    add_documentation: bool = True


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


def get_implementing_types(type: GraphQLInterfaceType, client_schema: GraphQLSchema):
    implementing_types = []
    for type in client_schema.get_implementing_types(type):
        implementing_types.append(type)
        implementing_types += get_implementing_types(type, client_schema)
    return implementing_types



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

    registry.register_fragment_type(f.name.value, type)




    if isinstance(type, GraphQLInterfaceType):

        implementing_types = client_schema.get_implementations(type)
    
        mother_class_fields = []
        base_fragment_name =  registry.style_fragment_class(f.name.value)
        additional_bases = get_additional_bases_for_type(type.name, config, registry)

        if type.description and plugin_config.add_documentation:
            mother_class_fields.append(
                ast.Expr(value=ast.Constant(value=type.description))
            )

        sub_nodes = non_typename_fields(f)

        mother_class_name = base_fragment_name + "Base"


        implementing_class_base_classes = {
        }


        inline_fragment_fields = {}



        for sub_node in sub_nodes:

            if isinstance(sub_node, FragmentSpreadNode):
                # Spread nodes are like inheritance?
                try:
                    # We are dealing with a fragment that is an interface
                    implementation_map = registry.get_interface_fragment_implementations(sub_node.name.value)
                    for k, v in implementation_map.items():
                        implementing_class_base_classes.setdefault(k, []).append(v)

                except KeyError:
                    x = registry.get_fragment_type(sub_node.name.value)
                    implementing_class_base_classes.setdefault(x, []).append(registry.inherit_fragment(sub_node.name.value))



            if isinstance(sub_node, FieldNode):

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

            if isinstance(sub_node, InlineFragmentNode):
                on_type_name = sub_node.type_condition.name.value

                inline_fragment_fields.setdefault(on_type_name, []).append(
                    generate_typename_field(
                        sub_node.type_condition.name.value, registry, config
                    )
                )


        mother_class = ast.ClassDef(
            mother_class_name,
            bases=additional_bases + get_interface_bases(config, registry) ,  # Todo: fill with base
            decorator_list=[],
            keywords=[],
            body=mother_class_fields if mother_class_fields else [ast.Pass()],
        )

        catch_class_name = f"{base_fragment_name}Catch"

        catch_class = ast.ClassDef(
            catch_class_name,
            bases=[ast.Name(id=mother_class_name, ctx=ast.Load())],  # Todo: fill with base
            decorator_list=[],
            keywords=[],
            body=[generate_generic_typename_field(registry, config)] + mother_class_fields,
        )



        tree.append(mother_class)
        tree.append(catch_class)



        implementaionMap = {}

        for i in implementing_types.objects:

            class_name = f"{base_fragment_name}{i.name}"


            ast_base_nodes = [ast.Name(id=x, ctx=ast.Load()) for x in implementing_class_base_classes.get(i, [])]
            implementaionMap[i.name] = class_name

            inline_fields = inline_fragment_fields.get(i, [])

            implementing_class = ast.ClassDef(
                    class_name,
                    bases=ast_base_nodes + [ast.Name(id=mother_class_name, ctx=ast.Load())] + get_interface_bases(config, registry),  # Todo: fill with base
                    decorator_list=[],
                    keywords=[],
                    body=[generate_typename_field(i.name, registry, config)] + inline_fields,
            )

            tree.append(implementing_class)


        registry.register_interface_fragment_implementations(f.name.value, implementaionMap)


        return tree


    elif isinstance(type, GraphQLObjectType):
        additional_bases = get_additional_bases_for_type(
            f.type_condition.name.value, config, registry
        )

        if type.description and plugin_config.add_documentation:
            fields.append(
                ast.Expr(value=ast.Constant(value=type.description))
            )

        fields += [generate_typename_field(type.name, registry, config)]

        for field in f.selection_set.selections:

            if field.name.value == "__typename":
                continue

            if isinstance(field, FragmentDefinitionNode):  # pragma: no cover

                continue

            if isinstance(field, FragmentSpreadNode):
                try:
                    implementationMap = registry.get_interface_fragment_implementations(field.name.value)
                    if type.name in implementationMap:
                        additional_bases = [
                            ast.Name(
                                id=implementationMap[type.name],
                                ctx=ast.Load(),
                            )
                        ] + additional_bases
                    else:
                        raise Exception(f"Could not find implementation for {type.name} in {implementationMap}")
                except KeyError:
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

    elif isinstance(type, GraphQLUnionType):
        base_fragment_name = registry.style_fragment_class(f.name.value)
        additional_bases = get_additional_bases_for_type(type.name, config, registry)

        sub_nodes = non_typename_fields(f)

        mother_class_name = base_fragment_name  # + "Base"

        member_class_base_classes = {}

        inline_fragment_fields = {}

        for sub_node in sub_nodes:

            if isinstance(sub_node, FragmentSpreadNode):
                # Spread nodes are like inheritance
                # We are dealing with a fragment that is a union
                implementation_map = registry.get_union_fragment_members(
                    sub_node.name.value
                )
                for k, v in implementation_map.items():
                    member_class_base_classes.setdefault(k, []).append(v)

            elif isinstance(sub_node, FieldNode):
                if sub_node.name.value == "__typename":
                    continue
                raise AssertionError("Union types should not have fields")

            elif isinstance(sub_node, InlineFragmentNode):
                on_type_name = sub_node.type_condition.name.value

                fields = []
                for field in sub_node.selection_set.selections:

                    if field.name.value == "__typename":
                        continue

                    if isinstance(field, FragmentSpreadNode):
                        member_class_base_classes.setdefault(on_type_name, []).append(
                            field.name.value
                        )
                        continue

                    field_type = client_schema.get_type(on_type_name)

                    field_definition = get_field_def(
                        client_schema, field_type, field
                    )
                    assert (
                        field_definition
                    ), f"Couldn't find field definition for {on_type_name}.{field.name.value}"

                    fields += type_field_node(
                        field,
                        name,
                        field_definition,
                        client_schema,
                        config,
                        tree,
                        registry,
                    )

                inline_fragment_fields.setdefault(on_type_name, []).extend(fields)
            else:
                raise AssertionError(f"Unknown node type: {type(sub_node)}")

        implementationMap = {}

        for i in type.types:

            class_name = f"{base_fragment_name}{i.name}"

            ast_base_nodes = [
                ast.Name(id=x, ctx=ast.Load())
                for x in member_class_base_classes.get(i.name, [])
            ]
            implementationMap[i.name] = class_name

            inline_fields = inline_fragment_fields.get(i.name, [])

            implementing_class = ast.ClassDef(
                class_name,
                bases=ast_base_nodes
                + get_fragment_bases(config, plugin_config, registry),
                decorator_list=[],
                keywords=[],
                body=[generate_typename_field(i.name, registry, config)]
                + inline_fields,
            )

            tree.append(implementing_class)

        registry.register_union_fragment_members(
            f.name.value, implementationMap
        )

        registry.register_import("typing.Union")
        mother_class = ast.Assign(
            targets=[ast.Name(id=base_fragment_name, ctx=ast.Load())],
            value=ast.Subscript(
                value=ast.Name(id="Union", ctx=ast.Load()),
                slice=ast.Tuple(
                    elts=[
                        ast.Name(id=f"{base_fragment_name}{i.name}", ctx=ast.Load())
                        for i in type.types
                    ],
                    ctx=ast.Load(),
                ),
            ),
            simple=1,
        )

        tree.append(mother_class)

        if type.description and plugin_config.add_documentation:
            tree.append(
                ast.Expr(value=ast.Constant(value=type.description))
            )

        return tree


def reorder_definitions(document, sorted_fragments):
    """Reorder document definitions to place fragments in dependency order."""
    fragment_definitions = {defn.name.value: defn for defn in document.definitions if isinstance(defn, FragmentDefinitionNode)}

    # Order fragments according to the topologically sorted order
    ordered_fragments = [fragment_definitions[name] for name in sorted_fragments if name in fragment_definitions]

    # Combine operations and ordered fragments
    return ordered_fragments


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

        # Find dependencies and sort fragments topologically
        fragment_dependencies = build_recursive_dependency_graph(documents)
       
        sorted_fragments = topological_sort(fragment_dependencies)
        


        ordered_fragments = reorder_definitions(documents, sorted_fragments)

        
        

        for fragment in ordered_fragments:
            plugin_tree += generate_fragment(
                fragment, client_schema, config, self.config, registry
            )

        return plugin_tree
