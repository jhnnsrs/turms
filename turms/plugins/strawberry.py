from graphql import (
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
    is_wrapping_type,
)
from turms.errors import GenerationError
from turms.plugins.base import Plugin, PluginConfig
import ast
from typing import Dict, List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from pydantic import Field
from graphql.type.definition import (
    GraphQLEnumType,
)
from turms.registry import ClassRegistry
from turms.utils import (
    generate_config_class,
    get_additional_bases_for_type,
    interface_is_extended_by_other_interfaces,
)
from turms.config import GraphQLTypes


class StrawberryPluginConfig(PluginConfig):
    type = "turms.plugins.strawberry.Strawberry"
    types_bases: List[str] = []
    inputtype_bases: List[str] = []
    skip_underscore: bool = True
    skip_double_underscore: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_STRAWBERRY_"


def generate_object_field_annotation(
    graphql_type: GraphQLType,
    parent: str,
    config: GeneratorConfig,
    plugin_config: StrawberryPluginConfig,
    registry: ClassRegistry,
    is_optional=True,
):
    if isinstance(graphql_type, GraphQLScalarType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(graphql_type.name),
                ctx=ast.Load(),
            )

        return registry.reference_scalar(graphql_type.name)

    if isinstance(graphql_type, GraphQLInterfaceType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_interface(graphql_type.name, parent),
                ctx=ast.Load(),
            )

        return registry.reference_interface(graphql_type.name, parent)

    if isinstance(graphql_type, GraphQLObjectType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_object(graphql_type.name, parent),
                ctx=ast.Load(),
            )
        return registry.reference_object(graphql_type.name, parent)

    if isinstance(graphql_type, GraphQLUnionType):
        if is_optional:
            registry.register_import("typing.Optional")
            registry.register_import("typing.Union")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("Union", ctx=ast.Load()),
                    slice=ast.Tuple(
                        elts=[
                            generate_object_field_annotation(
                                union_type,
                                parent,
                                config,
                                plugin_config,
                                registry,
                                is_optional=False,
                            )
                            for union_type in graphql_type.types
                        ],
                        ctx=ast.Load(),
                    ),
                ),
                ctx=ast.Load(),
            )
        registry.register_import("typing.Union")

        return ast.Subscript(
            value=ast.Name("Union", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[
                    generate_object_field_annotation(
                        union_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=False,
                    )
                    for union_type in graphql_type.types
                ],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        )

    if isinstance(graphql_type, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_enum(
                    graphql_type.name,
                    parent,
                    allow_forward=not config.force_plugin_order,
                ),
                ctx=ast.Load(),
            )
        return registry.reference_enum(
            graphql_type.name, parent, allow_forward=not config.force_plugin_order
        )

    if isinstance(graphql_type, GraphQLNonNull):
        return generate_object_field_annotation(
            graphql_type.of_type,
            parent,
            config,
            plugin_config,
            registry,
            is_optional=False,
        )

    if isinstance(graphql_type, GraphQLList):

        registry.register_import("typing.List")
        list_builder = lambda x: ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()), slice=x, ctx=ast.Load()
        )

        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=list_builder(
                    generate_object_field_annotation(
                        graphql_type.of_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    )
                ),
                ctx=ast.Load(),
            )

        registry.register_import("typing.List")
        return list_builder(
            generate_object_field_annotation(
                graphql_type.of_type,
                parent,
                config,
                plugin_config,
                registry,
                is_optional=True,
            )
        )

    raise NotImplementedError(f"Unknown input type {repr(graphql_type)}")


def recurse_argument_annotation(
    graphql_type: GraphQLType,
    parent: str,
    config: GeneratorConfig,
    plugin_config: StrawberryPluginConfig,
    registry: ClassRegistry,
    is_optional=True,
):
    if isinstance(graphql_type, GraphQLScalarType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(graphql_type.name),
                ctx=ast.Load(),
            )

        return registry.reference_scalar(graphql_type.name)

    if isinstance(graphql_type, GraphQLInputObjectType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_inputtype(graphql_type.name, parent),
                ctx=ast.Load(),
            )
        return registry.reference_inputtype(graphql_type.name, parent)

    if isinstance(graphql_type, GraphQLUnionType):
        if is_optional:
            registry.register_import("typing.Optional")
            registry.register_import("typing.Union")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("Union", ctx=ast.Load()),
                    slice=ast.Tuple(
                        elts=[
                            recurse_argument_annotation(
                                union_type,
                                parent,
                                config,
                                plugin_config,
                                registry,
                                is_optional=False,
                            )
                            for union_type in graphql_type.types
                        ],
                        ctx=ast.Load(),
                    ),
                ),
                ctx=ast.Load(),
            )
        registry.register_import("typing.Union")

        return ast.Subscript(
            value=ast.Name("Union", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[
                    generate_object_field_annotation(
                        union_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=False,
                    )
                    for union_type in graphql_type.types
                ],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        )

    if isinstance(graphql_type, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_enum(
                    graphql_type.name,
                    parent,
                    allow_forward=not config.force_plugin_order,
                ),
                ctx=ast.Load(),
            )
        return registry.reference_enum(
            graphql_type.name, parent, allow_forward=not config.force_plugin_order
        )

    if isinstance(graphql_type, GraphQLNonNull):
        return recurse_argument_annotation(
            graphql_type.of_type,
            parent,
            config,
            plugin_config,
            registry,
            is_optional=False,
        )

    if isinstance(graphql_type, GraphQLList):

        registry.register_import("typing.List")
        list_builder = lambda x: ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()), slice=x, ctx=ast.Load()
        )

        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=list_builder(
                    recurse_argument_annotation(
                        graphql_type.of_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    )
                ),
                ctx=ast.Load(),
            )

        registry.register_import("typing.List")
        return list_builder(
            generate_object_field_annotation(
                graphql_type.of_type,
                parent,
                config,
                plugin_config,
                registry,
                is_optional=True,
            )
        )

    raise NotImplementedError(f"Unknown input type {repr(graphql_type)}")


def generate_enums(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: StrawberryPluginConfig,
    registry: ClassRegistry,
):

    tree = []

    enum_types = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLEnumType)
    }

    registry.register_import("enum.Enum")

    decorator = ast.Name(id="strawberry.enum", ctx=ast.Load())

    for key, type in enum_types.items():

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        classname = registry.generate_enum(key)

        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

        for value_key, value in type.values.items():

            assign = ast.Assign(
                targets=[ast.Name(id=str(value_key), ctx=ast.Store())],
                value=ast.Constant(value=value.value),
            )

            potential_comment = (
                value.description
                if not value.deprecation_reason
                else f"DEPRECATED: {value.description}"
            )

            if potential_comment:
                fields += [
                    assign,
                    ast.Expr(value=ast.Constant(value=potential_comment)),
                ]

            else:
                fields += [assign]

        tree.append(
            ast.ClassDef(
                classname,
                bases=[
                    ast.Name(id="Enum", ctx=ast.Load()),
                ],
                decorator_list=[decorator],
                keywords=[],
                body=fields,
            )
        )

    return tree


def generate_inputs(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: StrawberryPluginConfig,
    registry: ClassRegistry,
):

    tree = []

    inputobjects_type = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLInputObjectType)
    }

    decorator = ast.Name(id="strawberry.input", ctx=ast.Load())

    for key, type in inputobjects_type.items():

        if plugin_config.skip_underscore and key.startswith("_"):  # pragma: no cover
            continue

        additional_bases = get_additional_bases_for_type(type.name, config, registry)
        name = registry.generate_inputtype(key)
        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

        for value_key, value in type.fields.items():
            value: GraphQLField

            keywords = []
            if value.description:
                keywords.append(
                    ast.keyword(
                        arg="description",
                        value=ast.Constant(value=value.description),
                    )
                )

            if value.deprecation_reason:
                keywords.append(
                    ast.keyword(
                        arg="deprecation_reason",
                        value=ast.Constant(value=value.deprecation_reason),
                    )
                )

            if keywords:
                assign_value = ast.Call(
                    func=ast.Name(
                        id="strawberry.field",
                        ctx=ast.Load(),
                    ),
                    keywords=keywords,
                    args=[],
                )
            else:
                assign_value = None

            assign = ast.AnnAssign(
                target=ast.Name(
                    registry.generate_node_name(value_key), ctx=ast.Store()
                ),
                annotation=recurse_argument_annotation(
                    value.type,
                    name,
                    config,
                    plugin_config,
                    registry,
                    is_optional=True,
                ),
                value=assign_value,
                simple=1,
            )

            fields += [assign]

        tree.append(
            ast.ClassDef(
                name,
                bases=additional_bases
                + [
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.inputtype_bases
                ],
                decorator_list=[decorator],
                keywords=[],
                body=fields
                + generate_config_class(GraphQLTypes.INPUT, config, typename=key),
            )
        )

    return tree


def generate_types(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: StrawberryPluginConfig,
    registry: ClassRegistry,
):

    tree = []

    objects = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLObjectType)
        and not isinstance(value, GraphQLInputObjectType)
        or isinstance(value, GraphQLInterfaceType)
    }

    sorted_objects = {
        k: v
        for k, v in sorted(
            objects.items(),
            key=lambda item: isinstance(item[1], GraphQLInterfaceType),
            reverse=True,
        )
    }
    registry.register_import("strawberry")

    interface_map: Dict[
        str, List[str]
    ] = {}  # A list of interfaces with the union classes attached
    interface_base_map: Dict[
        str, str
    ] = {}  # A list of interfaces with its respective base

    for key, object_type in sorted_objects.items():

        additional_bases = get_additional_bases_for_type(
            object_type.name, config, registry
        )

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        if plugin_config.skip_double_underscore and key.startswith("__"):
            continue

        if isinstance(object_type, GraphQLObjectType):
            classname = registry.generate_objecttype(key)
            decorator = ast.Name(id="strawberry.type", ctx=ast.Load())
        if isinstance(object_type, GraphQLInterfaceType):
            classname = registry.generate_interface(key)
            decorator = ast.Name(id="strawberry.interface", ctx=ast.Load())
            interface_base_map[key] = classname

        for interface in object_type.interfaces:
            # Populate the Union_classed
            interface_map.setdefault(interface.name, []).append(classname)

            other_interfaces = set(object_type.interfaces) - {interface}
            if not interface_is_extended_by_other_interfaces(
                interface, other_interfaces
            ):
                additional_bases.append(
                    ast.Name(
                        id=registry.inherit_interface(interface.name),
                        ctx=ast.Load(),
                    )
                )

        fields = (
            [ast.Expr(value=ast.Constant(value=object_type.description))]
            if object_type.description
            else []
        )

        if key in ["Query", "Mutation", "Subscription"]:
            for value_key, value in object_type.fields.items():
                value: GraphQLField

                keywords = []
                if value.description:
                    keywords.append(
                        ast.keyword(
                            arg="description",
                            value=ast.Constant(value=value.description),
                        )
                    )

                if value.deprecation_reason:
                    keywords.append(
                        ast.keyword(
                            arg="deprecation_reason",
                            value=ast.Constant(value=value.deprecation_reason),
                        )
                    )

                additional_args = []

                for argkey, arg in value.args.items():
                    additional_args.append(
                        ast.arg(
                            arg=registry.generate_parameter_name(argkey),
                            annotation=recurse_argument_annotation(
                                arg.type,
                                classname,
                                config,
                                plugin_config,
                                registry=registry,
                                is_optional=True,
                            ),
                        )
                    )

                body = []

                if value.description:
                    body.append(ast.Expr(value=ast.Constant(value=value.description)))

                body.append(ast.Return(value=ast.Constant(value=None)))

                returns = generate_object_field_annotation(
                    value.type,
                    classname,
                    config,
                    plugin_config,
                    registry,
                    is_optional=True,
                )

                if key == "Query":
                    assign_value = ast.Call(
                        func=ast.Name(
                            id="strawberry.field",
                            ctx=ast.Load(),
                        ),
                        keywords=keywords,
                        args=[],
                    )
                    function_def = ast.FunctionDef
                    returns = returns
                elif key == "Mutation":
                    assign_value = ast.Call(
                        func=ast.Name(
                            id="strawberry.mutation",
                            ctx=ast.Load(),
                        ),
                        keywords=keywords,
                        args=[],
                    )
                    function_def = ast.FunctionDef
                    returns = returns

                elif key == "Subscription":
                    registry.register_import("typing.AsyncGenerator")
                    assign_value = ast.Call(
                        func=ast.Name(
                            id="strawberry.subscription",
                            ctx=ast.Load(),
                        ),
                        keywords=keywords,
                        args=[],
                    )
                    function_def = ast.AsyncFunctionDef
                    returns = ast.Subscript(
                        value=ast.Name(id="AsyncGenerator", ctx=ast.Load()),
                        slice=ast.Tuple(
                            elts=[returns, ast.Name(id="None", ctx=ast.Load())]
                        ),
                        ctx=ast.Load(),
                    )

                assign = function_def(
                    name=registry.generate_node_name(value_key),
                    returns=returns,
                    args=ast.arguments(
                        args=[ast.arg(arg="self")] + additional_args,
                        posonlyargs=[],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=body,
                    decorator_list=[assign_value],
                    simple=1,
                )

                fields += [assign]

        else:
            for value_key, value in object_type.fields.items():
                value: GraphQLField

                keywords = []
                if value.description:
                    keywords.append(
                        ast.keyword(
                            arg="description",
                            value=ast.Constant(value=value.description),
                        )
                    )

                if value.deprecation_reason:
                    keywords.append(
                        ast.keyword(
                            arg="deprecation_reason",
                            value=ast.Constant(value=value.deprecation_reason),
                        )
                    )

                if keywords:
                    assign_value = ast.Call(
                        func=ast.Name(
                            id="strawberry.field",
                            ctx=ast.Load(),
                        ),
                        keywords=keywords,
                        args=[],
                    )
                else:
                    assign_value = None

                assign = ast.AnnAssign(
                    target=ast.Name(
                        registry.generate_node_name(value_key), ctx=ast.Store()
                    ),
                    annotation=generate_object_field_annotation(
                        value.type,
                        classname,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    ),
                    value=assign_value,
                    simple=1,
                )

                fields += [assign]

        tree.append(
            ast.ClassDef(
                classname,
                bases=additional_bases,
                decorator_list=[decorator],
                keywords=[],
                body=fields + generate_config_class(GraphQLTypes.OBJECT, config, key),
            )
        )

    return tree


class StrawberryPlugin(Plugin):
    """Generate Strawberry models for GraphQL objects

    This plugin generates Pydantic models for GraphQL ObjectTypes and Interfaces in your graphql schema.

    Attention: This plugin is not made for client side usage. Most likely you are looking for the
    operations, fragments and funcs plugin (that generates client side validation and query function
    for your documents (your operations, fragments and queries).


    """

    config: StrawberryPluginConfig = Field(default_factory=StrawberryPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        enums = generate_enums(client_schema, config, self.config, registry)
        inputs = generate_inputs(client_schema, config, self.config, registry)
        types = generate_types(client_schema, config, self.config, registry)

        return enums + inputs + types
