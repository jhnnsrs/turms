import ast
from typing import List, Optional

from pydantic_settings import SettingsConfigDict
from turms.config import GeneratorConfig
from graphql import GraphQLSchema, InputObjectTypeDefinitionNode
from graphql.language.ast import OperationDefinitionNode, OperationType
from turms.recurse import type_field_node
from turms.plugins.base import Plugin, PluginConfig
from pydantic import Field
from graphql.language.ast import (
    FieldNode,
    OperationDefinitionNode,
    OperationType,
)
from graphql.utilities.get_operation_root_type import get_operation_root_type
from graphql.utilities.type_info import get_field_def

import re
from graphql import NonNullTypeNode, VariableDefinitionNode, language
from turms.registry import ClassRegistry
from turms.utils import (
    generate_pydantic_config,
    inspect_operation_for_documentation,
    merge_bases_sequences,
    merge_body_sequences,
    parse_documents,
    recurse_type_annotation,
    replace_iteratively,
    parse_value_node,
)
import logging


logger = logging.getLogger(__name__)
fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


class OperationsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PLUGINS_OPERATIONS_")
    type: str = "turms.plugins.operations.OperationsPlugin"
    query_bases: List[str] = []
    arguments_bases: List[str] = []
    mutation_bases: List[str] = []
    subscription_bases: List[str] = []
    operations_glob: Optional[str] = None
    create_arguments: bool = True
    extract_documentation: bool = True
    arguments_allow_population_by_field_name: bool = False


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


def generate_arguments_config(
    o: OperationType,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):
    if config.pydantic_version == "1":
        config_fields = []

        if plugin_config.arguments_allow_population_by_field_name:
            config_fields.append(
                ast.Assign(
                    targets=[
                        ast.Name(id="allow_population_by_field_name", ctx=ast.Store())
                    ],
                    value=ast.Constant(value=True),
                )
            )

        if len(config_fields) > 0:
            return [
                ast.ClassDef(
                    name="Config",
                    bases=[],
                    keywords=[],
                    body=[
                        ast.Expr(
                            value=ast.Constant(value=" Arguments config class"),
                        )
                    ]
                    + config_fields,
                    decorator_list=[],
                )
            ]
        else:
            return []

    else:
        config_keywords = []

        if plugin_config.arguments_allow_population_by_field_name is not None:
            config_keywords.append(
                ast.keyword(
                    arg="populate_by_name",
                    value=ast.Constant(
                        value=config.options.allow_population_by_field_name
                    ),
                )
            )

        if len(config_keywords) > 0:
            registry.register_import("pydantic.ConfigDict")
            return [
                ast.Assign(
                    targets=[ast.Name(id="model_config", ctx=ast.Store())],
                    value=ast.Call(
                        func=ast.Name(id="ConfigDict", ctx=ast.Load()),
                        args=[],
                        keywords=config_keywords,
                    ),
                )
            ]
        else:
            return []


def get_arguments_bases(
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
) -> List[ast.Name]:
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


def generate_operation(
    o: OperationDefinitionNode,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: OperationsPluginConfig,
    registry: ClassRegistry,
):
    tree = []
    if o.name is None:
        raise ValueError(
            "Operation name is required. Please provide a name for the operation."
        )

    # Generation means creating a class for the operation
    if o.operation == OperationType.MUTATION:
        class_name = registry.generate_mutation(o.name.value)
        extra_bases = get_mutation_bases(config, plugin_config, registry)
    elif o.operation == OperationType.SUBSCRIPTION:
        class_name = registry.generate_subscription(o.name.value)
        extra_bases = get_subscription_bases(config, plugin_config, registry)
    elif o.operation == OperationType.QUERY:
        class_name = registry.generate_query(o.name.value)
        extra_bases = get_query_bases(config, plugin_config, registry)
    else:
        raise ValueError(
            f"Unsupported operation type: {o.operation}. Supported types are: QUERY, MUTATION, SUBSCRIPTION."
        )

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
                value=ast.Constant(value=operation_documentation),
            )
        )
    else:
        class_body_fields.append(
            ast.Expr(
                value=ast.Constant(value="No documentation found for this operation."),
            )
        )

    operation_annotations: list[ast.AnnAssign] = []

    for field_node in o.selection_set.selections:
        if isinstance(field_node, FieldNode):
            field_definition = get_field_def(client_schema, x, field_node)
            assert field_definition, "Couldn't find field definition"

            generated_node = type_field_node(
                field_node,
                class_name,
                field_definition,
                client_schema,
                config,
                tree,
                registry,
            )

            type_annotation = generated_node[0]
            if isinstance(type_annotation, ast.AnnAssign):
                operation_annotations.append(type_annotation)
            else:
                raise ValueError(
                    f"Expected type annotation to be of type ast.AnnAssign, got {type(type_annotation)}"
                )

            class_body_fields += generated_node

        else:
            raise ValueError(f"Unsupported selection set node type: {type(field_node)}")

    if len(operation_annotations) == 1:
        # "Has only one root operation -> Registering as a single operation"
        registry.register_operation_single(
            o.name.value, operation_annotations[0].annotation
        )

    query_document = language.print_ast(o)
    merged_document = replace_iteratively(query_document, registry)

    if plugin_config.create_arguments:
        arguments_body = []

        for v in o.variable_definitions:
            is_optional = not isinstance(v.type, NonNullTypeNode) or v.default_value
            annotation = recurse_type_annotation(v.type, registry)
            field_name = registry.generate_parameter_name(v.variable.name.value)
            target = v.variable.name.value

            if target != field_name:
                registry.register_import("pydantic.Field")
                if is_optional:
                    assign = ast.AnnAssign(
                        target=ast.Name(field_name, ctx=ast.Store()),
                        annotation=annotation,
                        value=ast.Call(
                            func=ast.Name(id="Field", ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(
                                    arg="alias", value=ast.Constant(value=target)
                                ),
                                ast.keyword(
                                    arg="default",
                                    value=ast.Constant(
                                        value=(
                                            parse_value_node(v.default_value)
                                            if v.default_value is not None
                                            else None
                                        )
                                    ),
                                ),
                            ],
                        ),
                        simple=1,
                    )
                else:
                    assign = ast.AnnAssign(
                        target=ast.Name(field_name, ctx=ast.Store()),
                        annotation=annotation,
                        value=ast.Call(
                            func=ast.Name(id="Field", ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(
                                    arg="alias", value=ast.Constant(value=target)
                                )
                            ],
                        ),
                        simple=1,
                    )
            else:
                if is_optional:
                    assign = ast.AnnAssign(
                        target=ast.Name(field_name, ctx=ast.Store()),
                        annotation=annotation,
                        value=ast.Call(
                            func=ast.Name(id="Field", ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(
                                    arg="default",
                                    value=ast.Constant(
                                        value=(
                                            parse_value_node(v.default_value)
                                            if v.default_value is not None
                                            else None
                                        )
                                    ),
                                ),
                            ],
                        ),
                        simple=1,
                    )
                else:
                    assign = ast.AnnAssign(
                        target=ast.Name(field_name, ctx=ast.Store()),
                        annotation=annotation,
                        simple=1,
                    )

            arguments_body += [assign]

        arguments_body += generate_arguments_config(
            o.operation, config, plugin_config, registry
        )

        class_body_fields += [
            ast.ClassDef(
                "Arguments",
                bases=merge_bases_sequences(
                    get_arguments_bases(config, plugin_config, registry=registry)
                ),
                decorator_list=[],
                keywords=[],
                type_params=[],
                body=merge_body_sequences(
                    [
                        ast.Expr(
                            value=ast.Constant(value=f"Arguments for {o.name.value} "),
                        )
                    ],
                    arguments_body or [ast.Pass()],
                ),
            )
        ]

    meta_body = [
        ast.Expr(
            value=ast.Constant(value=f"Meta class for {o.name.value} "),
        ),
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
        ast.ClassDef(
            "Meta",
            bases=[],
            decorator_list=[],
            keywords=[],
            body=meta_body,
            type_params=[],
        ),
    ]

    tree.append(
        ast.ClassDef(
            class_name,
            bases=merge_bases_sequences(extra_bases),
            decorator_list=[],
            keywords=[],
            type_params=[],
            body=merge_body_sequences(
                class_body_fields,
                generate_pydantic_config(o.operation, config, registry),
            ),
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

        glob = self.config.operations_glob or config.documents

        if not glob:
            raise ValueError(
                "No documents found. Please provide a glob pattern for the documents."
            )

        documents = parse_documents(client_schema, glob)

        definitions = documents.definitions
        operations = [
            node for node in definitions if isinstance(node, OperationDefinitionNode)
        ]

        for operation in operations:
            plugin_tree += generate_operation(
                operation, client_schema, config, self.config, registry
            )

        return plugin_tree
