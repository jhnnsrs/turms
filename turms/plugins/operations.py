import ast
from typing import List, Optional
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.language.ast import OperationDefinitionNode, OperationType
from turms.recurse import type_field_node
from turms.plugins.base import Plugin, PluginConfig
from pydantic import Field
from graphql.language.ast import (
    FieldNode,
    OperationDefinitionNode,
    OperationType,
    VariableDefinitionNode,
    NamedTypeNode,
    ListTypeNode,
)
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.utilities.get_operation_root_type import get_operation_root_type
from graphql.utilities.type_info import get_field_def

import re
from graphql import NonNullTypeNode, language
from turms.registry import ClassRegistry
from turms.utils import (
    generate_config_class,
    inspect_operation_for_documentation,
    parse_documents,
    recurse_type_annotation,
    replace_iteratively,
    parse_value_node,
)
import logging
from turms.utils import print_operation

logger = logging.getLogger(__name__)
fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


class OperationsPluginConfig(PluginConfig):
    type = "turms.plugins.operations.OperationsPlugin"
    query_bases: List[str] = None
    arguments_bases: List[str] = None
    mutation_bases: List[str] = None
    subscription_bases: List[str] = None
    operations_glob: Optional[str]
    create_arguments: bool = True
    extract_documentation: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_OPERATIONS_"


def get_query_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.query_bases:
        for base in plugin_config.query_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.query_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def get_mutation_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.mutation_bases:
        for base in plugin_config.mutation_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.mutation_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def get_arguments_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.arguments_bases:
        for base in plugin_config.arguments_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.arguments_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def get_subscription_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    if plugin_config.subscription_bases:
        for base in plugin_config.subscription_bases:
            registry.register_import(base)

        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.subscription_bases
        ]
    else:
        for base in config.object_bases:
            registry.register_import(base)

            return [
                ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                for base in config.object_bases
            ]


def represent_variable_definition(x: VariableDefinitionNode)-> str:
    if isinstance(x, NamedTypeNode):
        return x.name.value
    if isinstance(x, NonNullTypeNode):
        return f"{represent_variable_definition(x.type)}!"
    if isinstance(x, ListTypeNode):
        return f"[{represent_variable_definition(x.type)}]"
    raise Exception(f"Unknown type {type(x)}")

def generate_operation(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):

    tree = []
    assert o.name.value, "Operation names are required"

    # Generation means creating a class for the operation
    if o.operation == OperationType.MUTATION:
        class_name = registry.generate_mutation(o.name.value)
        extra_bases = get_mutation_bases(config, plugin_config, registry)
    if o.operation == OperationType.SUBSCRIPTION:
        class_name = registry.generate_subscription(o.name.value)
        extra_bases = get_subscription_bases(config, plugin_config, registry)
    if o.operation == OperationType.QUERY:
        class_name = registry.generate_query(o.name.value)
        extra_bases = get_query_bases(config, plugin_config, registry)

    x = get_operation_root_type(client_schema, o)
    class_body_fields = []

    operation_documentation = (
        inspect_operation_for_documentation(o)
        if plugin_config.extract_documentation
        else None
    )
    if operation_documentation:
        class_body_fields.append(
            ast.Expr(
                value=ast.Str(s=operation_documentation),
            )
        )

    for field_node in o.selection_set.selections:
        field_node: FieldNode = field_node
        field_definition = get_field_def(client_schema, x, field_node)
        assert field_definition, "Couldn't find field definition"

        class_body_fields += [
            type_field_node(
                field_node,
                class_name,
                field_definition,
                client_schema,
                config,
                tree,
                registry,
            ),
        ]

    merged_document = print_operation(o, config, registry)

    if plugin_config.create_arguments:

        arguments_body = []
        validators_body = []

        for v in o.variable_definitions:

            variable_def_body = []

            type = v.type

            keywords = []

            if v.default_value:
                keywords.append(ast.keyword(arg="default", value=ast.Constant(v.default_value.value, ctx=ast.Load())))
                

            if keywords:
                registry.register_import("pydantic.Field")
                variable_def_body += [
                    ast.AnnAssign(
                        target=ast.Name(
                            id=registry.generate_parameter_name(v.variable.name.value),
                            ctx=ast.Store(),
                        ),
                        annotation=recurse_type_annotation(
                            v.type,
                            registry,
                        ),
                        value=ast.Call(
                            func=ast.Name(id="Field", ctx=ast.Load()),
                            args=[],
                            keywords=keywords,
                        ),
                        simple=1,
                    )
                ]
                
            else:
                variable_def_body += [
                    ast.AnnAssign(
                        target=ast.Name(
                            id=registry.generate_parameter_name(v.variable.name.value),
                            ctx=ast.Store(),
                        ),
                        annotation=recurse_type_annotation(v.type, registry),
                        simple=1,
                    )
                ]

            for directive in v.directives:
                directive_name = directive.name.value
                directive_def = registry.get_directive(directive_name)
                if directive_def:
                    variable_def_body = directive_def.type(
                        v,
                        variable_def_body,
                        registry,
                        **{arg.name.value: arg.value.value for arg in directive.arguments}
                    )
                    
            arguments_body += variable_def_body

        arguments_body += validators_body

        class_body_fields += [
            ast.ClassDef(
                "Arguments",
                bases=get_arguments_bases(config, plugin_config, registry=registry),
                decorator_list=[],
                keywords=[],
                body=arguments_body or [ast.Pass()],
            )
        ]

    meta_body = [
        ast.Assign(
            targets=[ast.Name(id="document", ctx=ast.Store())],
            value=ast.Constant(value=merged_document),
        ),
    ]
    if config.domain:
        meta_body += [
            ast.Assign(
                targets=[ast.Name(id="domain", ctx=ast.Store())],
                value=ast.Constant(value=str(config.domain)),
            )
        ]

    class_body_fields += [
        ast.ClassDef("Meta", bases=[], decorator_list=[], keywords=[], body=meta_body)
    ]

    tree.append(
        ast.ClassDef(
            class_name,
            bases=extra_bases,
            decorator_list=[],
            keywords=[],
            body=class_body_fields + generate_config_class(o.operation, config),
        )
    )

    return tree


class OperationsPlugin(Plugin):
    """ " Generate operations as classes

    This plugin created classes for operations. It will scan your documents and create classes for each operation.
    The class will have a `document` attribute that contains the query document, as well as contained "Arguments" class
    with the variables for the operation.

    This allows for the serialization of values in both directions.

    If you want to generate python functions instead, use the `funcs` plugin in ADDITION to this plugin.

    """

    config: OperationsPluginConfig = Field(default_factory=OperationsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        plugin_tree = []

        documents = parse_documents(
            client_schema, self.config.operations_glob or config.documents
        )

        definitions = documents.definitions
        operations = [
            node for node in definitions if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            plugin_tree += generate_operation(
                operation, client_schema, config, self.config, registry
            )

        return plugin_tree
