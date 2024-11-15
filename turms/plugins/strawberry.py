from graphql import (
    BooleanValueNode,
    ConstListValueNode,
    ConstObjectValueNode,
    ConstValueNode,
    EnumValueNode,
    FloatValueNode,
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
    IntValueNode,
    ListValueNode,
    NullValueNode,
    ObjectValueNode,
    StringValueNode,
    Undefined,
    GraphQLArgument,
    ObjectTypeDefinitionNode,
)
from pydantic_settings import SettingsConfigDict

from turms.plugins.base import Plugin, PluginConfig
import ast
from typing import Dict, List, Protocol, runtime_checkable
from turms.config import GeneratorConfig, ImportableFunctionMixin
from graphql.utilities.build_client_schema import GraphQLSchema
from pydantic import Field
from graphql.type.definition import (
    GraphQLEnumType,
)
from turms.registry import ClassRegistry
from turms.utils import (
    generate_pydantic_config,
    get_additional_bases_for_type,
    interface_is_extended_by_other_interfaces,
)
from turms.config import GraphQLTypes


@runtime_checkable
class StrawberryGenerateFunc(ImportableFunctionMixin, Protocol):
    def __call__(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        plugin_config: "StrawberryPluginConfig",
        registry: ClassRegistry,
    ) -> List[ast.AST]: ...  # pragma: no cover


def build_directive_type_annotation(value: GraphQLType, registry: ClassRegistry, is_optional=True):

    if isinstance(value, GraphQLScalarType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(value.name),
                ctx=ast.Load(),
            )
        
        return registry.reference_scalar(value.name)
    if isinstance(value, GraphQLObjectType):
        raise NotImplementedError("Object types cannot be used as arguments")
    if isinstance(value, GraphQLInterfaceType):
        raise NotImplementedError("Interface types cannot be used as arguments")
    if isinstance(value, GraphQLUnionType):
        raise NotImplementedError("Union types cannot be used as arguments")
    if isinstance(value, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_enum(value.name),
                ctx=ast.Load(),
            )

        return registry.reference_enum(value.name)
    if isinstance(value, GraphQLNonNull):
        return build_directive_type_annotation(value.of_type, registry, is_optional=False)
    if isinstance(value, GraphQLList):
        registry.register_import("typing.List")

        if is_optional:
            registry.register_import("typing.Optional")

            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("List", ctx=ast.Load()),
                    slice=build_directive_type_annotation(value.of_type, registry, is_optional=True),
                    ctx=ast.Load(),
                ),
                ctx=ast.Load(),
            )

        return ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()),
            slice=build_directive_type_annotation(value.of_type, registry, is_optional=True),
            ctx=ast.Load(),
        )
    if isinstance(value, GraphQLInputObjectType):
        raise NotImplementedError("Input types cannot be used as arguments")
    
    raise NotImplementedError(f"Unknown type {repr(value)}")



def convert_valuenode_to_ast(value: ConstValueNode):
    if isinstance(value, NullValueNode):
        return ast.Constant(value=None)
    if isinstance(value, StringValueNode):
        return ast.Constant(value=value.value)
    if isinstance(value, IntValueNode):
        return ast.Constant(value=value.value)
    if isinstance(value, FloatValueNode):
        return ast.Constant(value=value.value)
    if isinstance(value, BooleanValueNode):
        return ast.Constant(value=value.value)

    if isinstance(value, EnumValueNode):
        return ast.Constant(value=value)
    if isinstance(value, ListValueNode):
        return ast.List(elts=[convert_valuenode_to_ast(x) for x in value.values], ctx=ast.Load())
    if isinstance(value, ObjectValueNode):

        keys = []
        values = []

        for field in value.fields:
            keys.append(field.name.value)
            values.append(convert_valuenode_to_ast(field.value))

        return ast.Dict(
            keys=keys,
            values=values,
        )
    
    raise NotImplementedError(f"Unknown default value {repr(value)}")

    

def convert_default_value_to_ast(value):
    if value is Undefined:
        return None
    if value is None:
        return ast.Constant(value=None)
    if isinstance(value, str):
        return ast.Constant(value=value)
    if isinstance(value, int):
        return ast.Constant(value=value)
    if isinstance(value, float):
        return ast.Constant(value=value)
    if isinstance(value, bool):
        return ast.Constant(value=value)
    if isinstance(value, list):
        return ast.List(elts=[convert_default_value_to_ast(x) for x in value], ctx=ast.Load())
    if isinstance(value, dict):
        keys = []
        values = []

        for key, value in value.items():
            keys.append(key)
            values.append(convert_default_value_to_ast(value))

        return ast.Dict(
            keys=keys,
            values=values,
        )
    raise NotImplementedError(f"Unknown default value {repr(value)}")







def default_generate_directives(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: "StrawberryPluginConfig",
    registry: ClassRegistry,
):
    tree = []

    directives = client_schema.directives

    generatable_directives = [
        directive
        for directive in directives
        if directive.name not in plugin_config.builtin_directives
    ]

    if not generatable_directives:
        return []

    registry.register_import("strawberry.schema_directive.Location")

    for directive in generatable_directives:
        if plugin_config.skip_underscore and directive.name.startswith("_"):
            continue

        if plugin_config.skip_double_underscore and directive.name.startswith("__"):
            continue

        keywords = []
        fields = []

        keywords.append(
            ast.keyword(
                arg="locations",
                value=ast.List(
                    elts=[
                        ast.Attribute(
                            value=ast.Name(id="Location", ctx=ast.Load()),
                            attr=location.name,
                            ctx=ast.Load(),
                        )
                        for location in directive.locations
                    ],
                    ctx=ast.Load(),
                ),
            )
        )

        for value_key, value in directive.args.items():
            value: GraphQLArgument

            type = value.type

            if value.default_value is not None:
                default = convert_default_value_to_ast(value.default_value)
            else:
                default = None

            needs_factory = False
            if isinstance(default, ast.List):
                needs_factory = True
            if isinstance(default, ast.Dict):
                needs_factory = True


            field_value = None

            if default:
                if needs_factory:
                    field_value = ast.Call(
                        func=ast.Name(id="strawberry.field", ctx=ast.Load()),
                        keywords=[
                            ast.keyword(
                                arg="default_factory",
                                value=ast.Lambda(
                                    args=[], body=default
                                ),
                            ),
                        ],
                        args=[],
                    )
                else:
                    field_value = ast.Call(
                        func=ast.Name(id="strawberry.field", ctx=ast.Load()),
                        keywords=[
                            ast.keyword(
                                arg="default",
                                value=default,
                            ),
                        ],
                        args=[],
                    )


            assign = ast.AnnAssign(
                target=ast.Name(
                    id=registry.generate_node_name(value_key), ctx=ast.Store()
                ),
                annotation=build_directive_type_annotation(type, registry),
                value=field_value,
                simple=1,
            )

            fields += [assign]

        decorator = ast.Call(
            func=ast.Name(
                id="strawberry.schema_directive",
                ctx=ast.Load(),
            ),
            keywords=keywords,
            args=[],
        )

        tree.append(
            ast.ClassDef(
                name=directive.name,
                bases=[],
                decorator_list=[decorator],
                keywords=[],
                body=(fields or [ast.Pass()])
                + generate_pydantic_config(
                    GraphQLTypes.DIRECTIVE, config, registry, directive.name
                ),
            )
        )

    return tree


def default_generate_enums(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: "StrawberryPluginConfig",
    registry: ClassRegistry,
):
    tree = []

    enum_types = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLEnumType)
    }

    for key, type in enum_types.items():
        directive_keywords = generate_directive_keywords(type.ast_node, plugin_config)
        if directive_keywords:
            decorator = ast.Call(
                func=ast.Name(id="strawberry.enum", ctx=ast.Load()),
                keywords=directive_keywords,
                args=[],
            )
        else:
            decorator = ast.Name(id="strawberry.enum", ctx=ast.Load())

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        if plugin_config.skip_double_underscore and key.startswith("__"):
            continue

        classname = registry.generate_enum(key)

        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else []
        )

        for value_key, value in type.values.items():
            if isinstance(value.value, str):
                servalue = value.value
            else:
                servalue = value.value.value

            assign = ast.Assign(
                targets=[ast.Name(id=str(value_key), ctx=ast.Store())],
                value=ast.Constant(value=servalue),
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

        registry.register_import("enum.Enum")

        tree.append(
            ast.ClassDef(
                classname,
                bases=[
                    ast.Name(id="Enum", ctx=ast.Load()),
                ],
                decorator_list=[decorator],
                keywords=[],
                body=fields or [ast.Pass()],
            )
        )

    return tree


class StrawberryPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PLUGINS_STRAWBERRY_")
    type: str = "turms.plugins.strawberry.Strawberry"
    generate_directives: bool = True
    generate_scalars: bool = True
    builtin_directives: List[str] = ["include", "skip", "deprecated", "specifiedBy"]
    builtin_scalars: List[str] = ["String", "Boolean", "DateTime", "Int", "Float", "ID"]
    generate_enums: bool = True
    generate_types: bool = True
    generate_inputs: bool = True
    types_bases: List[str] = []
    inputtype_bases: List[str] = []
    skip_underscore: bool = False
    skip_double_underscore: bool = True

    # Functional configuration:
    generate_directives_func: StrawberryGenerateFunc = default_generate_directives
    generate_enums_func: StrawberryGenerateFunc = default_generate_enums


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

        def list_builder(x):
            return ast.Subscript(
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

    raise NotImplementedError(
        f"Unknown object type {repr(graphql_type)}"
    )  # pragma: no cover


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

        def list_builder(x):
            return ast.Subscript(
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
            recurse_argument_annotation(
                graphql_type.of_type,
                parent,
                config,
                plugin_config,
                registry,
                is_optional=True,
            )
        )

    raise NotImplementedError(f"Unknown input type {repr(graphql_type)}")


def generate_directive_keywords(
    ast_node: ObjectTypeDefinitionNode, plugin_config: StrawberryPluginConfig
):
    if not ast_node:
        return []

    directives = [
        directive
        for directive in ast_node.directives
        if directive.name.value not in plugin_config.builtin_directives
    ]

    if directives:
        calls = [
            ast.Call(
                func=ast.Name(
                    id=directive.name.value,
                    ctx=ast.Load(),
                ),
                keywords=[
                    ast.keyword(arg=arg.name.value, value=convert_valuenode_to_ast(arg.value))
                    for arg in directive.arguments
                ],
                args=[],
            )
            for directive in directives
        ]

        return [
            ast.keyword(
                arg="directives",
                value=ast.List(elts=calls, ctx=ast.Load()),
            )
        ]

    return []


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

    for key, type in inputobjects_type.items():
        if plugin_config.skip_underscore and key.startswith("_"):  # pragma: no cover
            continue

        directive_keywords = generate_directive_keywords(type.ast_node, plugin_config)
        if directive_keywords:
            decorator = ast.Call(
                func=ast.Name(id="strawberry.input", ctx=ast.Load()),
                keywords=directive_keywords,
                args=[],
            )
        else:
            decorator = ast.Name(id="strawberry.input", ctx=ast.Load())

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
                + generate_pydantic_config(
                    GraphQLTypes.INPUT, config, registry, typename=key
                ),
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

    interface_map: Dict[str, List[str]] = (
        {}
    )  # A list of interfaces with the union classes attached
    interface_base_map: Dict[str, str] = (
        {}
    )  # A list of interfaces with its respective base

    for key, object_type in sorted_objects.items():
        additional_bases = get_additional_bases_for_type(
            object_type.name, config, registry
        )

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        if plugin_config.skip_double_underscore and key.startswith("__"):
            continue

        directive_keywords = generate_directive_keywords(
            object_type.ast_node, plugin_config
        )

        if isinstance(object_type, GraphQLObjectType):
            classname = registry.generate_objecttype(key)
            decorator_name = "strawberry.type"
        if isinstance(object_type, GraphQLInterfaceType):
            classname = registry.generate_interface(key, with_base=False)
            decorator_name = "strawberry.interface"
            interface_base_map[key] = classname

        if directive_keywords:
            decorator = ast.Call(
                func=ast.Name(id=decorator_name, ctx=ast.Load()),
                keywords=directive_keywords,
                args=[],
            )
        else:
            decorator = ast.Name(id=decorator_name, ctx=ast.Load())

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
            kwdefaults = []
            if value.args:
                sorted_args = {
                    key: value
                    for key, value in sorted(
                        value.args.items(),
                        key=lambda item: item[1].default_value == Undefined,
                        reverse=True,
                    )
                }

                for argkey, arg in sorted_args.items():
                    additional_args.append(
                        ast.arg(
                            arg=registry.generate_parameter_name(argkey),
                            annotation=recurse_argument_annotation(
                                arg.type,
                                classname,
                                config,
                                plugin_config,
                                registry=registry,
                                is_optional=arg.default_value == Undefined,
                            ),
                        )
                    )

                    if arg.default_value != Undefined:
                        kwdefaults.append(ast.Constant(value=arg.default_value))

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

            keywords += generate_directive_keywords(value.ast_node, plugin_config)

            if not additional_args and key not in ["Mutation", "Subscription", "Query"]:
                if not keywords:
                    assign_value = None
                else:
                    assign_value = ast.Call(
                        func=ast.Name(
                            id="strawberry.field",
                            ctx=ast.Load(),
                        ),
                        keywords=keywords,
                        args=[],
                    )

                # lets create a simple field
                assign = ast.AnnAssign(
                    target=ast.Name(
                        registry.generate_node_name(value_key), ctx=ast.Store()
                    ),
                    annotation=returns,
                    value=assign_value,
                    simple=1,
                )

            else:
                if key == "Mutation":
                    decorator_name = ast.Name(id="strawberry.mutation", ctx=ast.Load())
                    function_def = ast.FunctionDef
                    returns = returns
                elif key == "Subscription":
                    registry.register_import("typing.AsyncGenerator")
                    decorator_name = ast.Name(
                        id="strawberry.subscription", ctx=ast.Load()
                    )
                    function_def = ast.AsyncFunctionDef
                    returns = ast.Subscript(
                        value=ast.Name(id="AsyncGenerator", ctx=ast.Load()),
                        slice=ast.Tuple(
                            elts=[returns, ast.Name(id="None", ctx=ast.Load())]
                        ),
                        ctx=ast.Load(),
                    )
                else:
                    decorator_name = ast.Name(id="strawberry.field", ctx=ast.Load())
                    function_def = ast.FunctionDef
                    returns = returns

                field_decorator = ast.Call(
                    func=decorator_name,
                    keywords=keywords,
                    args=[],
                )

                assign = function_def(
                    name=registry.generate_node_name(value_key),
                    returns=returns,
                    args=ast.arguments(
                        args=[ast.arg(arg="self")] + additional_args,
                        posonlyargs=[],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=kwdefaults,
                    ),
                    body=body,
                    decorator_list=[field_decorator],
                    simple=1,
                )

            fields += [assign]

        tree.append(
            ast.ClassDef(
                classname,
                bases=additional_bases,
                decorator_list=[decorator],
                keywords=[],
                body=fields
                + generate_pydantic_config(GraphQLTypes.OBJECT, config, registry, key),
            )
        )

    return tree


def generate_scalars(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: StrawberryPluginConfig,
    registry: ClassRegistry,
):
    objects = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLScalarType)
        and key not in plugin_config.builtin_scalars
    }

    tree = []

    if objects:
        registry.register_import("typing.NewType")

    for key, scalar in objects.items():
        keywords = []
        keywords += generate_directive_keywords(scalar.ast_node, plugin_config)
        if scalar.description:
            keywords.append(
                ast.keyword(
                    arg="description",
                    value=ast.Constant(value=scalar.description),
                )
            )

        keywords.append(
            ast.keyword(
                arg="serialize",
                value=ast.Lambda(
                    args=[
                        ast.arg(
                            arg="value",
                        ),
                    ],
                    body=ast.Name(id="value", ctx=ast.Load()),
                ),
            )
        )

        keywords.append(
            ast.keyword(
                arg="parse_value",
                value=ast.Lambda(
                    args=[
                        ast.arg(
                            arg="value",
                        ),
                    ],
                    body=ast.Name(id="value", ctx=ast.Load()),
                ),
            )
        )

        tree.append(
            ast.Assign(
                targets=[ast.Name(id=key, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(
                        id="strawberry.scalar",
                        ctx=ast.Load(),
                    ),
                    keywords=keywords,
                    args=[
                        ast.Call(
                            func=ast.Name(id="NewType", ctx=ast.Load()),
                            args=[
                                ast.Constant(value=key),
                                ast.Name(id="str", ctx=ast.Load()),
                            ],
                            keywords=[],
                        ),
                    ],
                ),
            )
        )
        registry.register_scalar(key, key)

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
        registry.register_import("strawberry")

        directives = (
            self.config.generate_directives_func(
                client_schema, config, self.config, registry
            )
            if self.config.generate_directives
            else []
        )

        scalars = (
            generate_scalars(client_schema, config, self.config, registry)
            if self.config.generate_directives
            else []
        )

        enums = (
            self.config.generate_enums_func(
                client_schema, config, self.config, registry
            )
            if self.config.generate_enums
            else []
        )
        inputs = (
            generate_inputs(client_schema, config, self.config, registry)
            if self.config.generate_inputs
            else []
        )
        types = (
            generate_types(client_schema, config, self.config, registry)
            if self.config.generate_types
            else []
        )

        return directives + scalars + enums + inputs + types
