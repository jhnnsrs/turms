from graphql import (
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
)
from turms.plugins.base import Plugin, PluginConfig
import ast
from typing import List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from turms.plugins.base import Plugin
from pydantic import Field
from graphql.type.definition import (
    GraphQLEnumType,
)
from turms.registry import ClassRegistry
from turms.utils import get_additional_bases_for_type


class ObjectsPluginConfig(PluginConfig):
    type = "turms.plugins.objects.ObjectsPlugin"
    types_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = False
    skip_double_underscore: bool = True

    class Config:
        env_prefix = "TURMS_PLUGINS_OBJECTS_"


def generate_object_field_annotation(
    graphql_type: GraphQLType,
    config: GeneratorConfig,
    plugin_config: ObjectsPluginConfig,
    registry: ClassRegistry,
    is_optional=True,
):
    if isinstance(graphql_type, GraphQLScalarType):
        registry.check_builtin_imports(graphql_type.name)
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Name(
                    id=registry.get_scalar_equivalent(graphql_type.name), ctx=ast.Load()
                ),
            )
        else:
            return ast.Name(
                id=registry.get_scalar_equivalent(graphql_type.name),
                ctx=ast.Load(),
            )

    if isinstance(graphql_type, GraphQLInterfaceType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(
                    value=registry.generate_interface_classname(graphql_type.name)
                ),
            )
        return ast.Constant(
            value=registry.generate_interface_classname(graphql_type.name),
        )

    if isinstance(graphql_type, GraphQLObjectType):
        registry.check_builtin_imports(graphql_type.name)
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(
                    value=registry.generate_objecttype_classname(graphql_type.name)
                ),
            )
        return ast.Constant(
            value=registry.generate_objecttype_classname(graphql_type.name),
        )

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
            )
        registry.register_import("typing.Union")

        return ast.Subscript(
            value=ast.Name("Union", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[
                    generate_object_field_annotation(
                        union_type,
                        config,
                        plugin_config,
                        registry,
                        is_optional=False,
                    )
                    for union_type in graphql_type.types
                ],
                ctx=ast.Load(),
            ),
        )

    if isinstance(graphql_type, GraphQLEnumType):
        registry.check_builtin_imports(graphql_type.name)
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Constant(
                    value=registry.get_enum_class(graphql_type.name),
                ),
            )
        return ast.Constant(
            value=registry.get_enum_class(graphql_type.name),
        )
    if isinstance(graphql_type, GraphQLNonNull):
        return generate_object_field_annotation(
            graphql_type.of_type, config, plugin_config, registry, is_optional=False
        )

    if isinstance(graphql_type, GraphQLList):
        if is_optional:
            registry.register_import("typing.Optional")
            registry.register_import("typing.List")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=ast.Subscript(
                    value=ast.Name("List", ctx=ast.Load()),
                    slice=generate_object_field_annotation(
                        graphql_type.of_type,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    ),
                    ctx=ast.Load(),
                ),
            )

        registry.register_import("typing.List")
        return ast.Subscript(
            value=ast.Name("List", ctx=ast.Load()),
            slice=generate_object_field_annotation(
                graphql_type.of_type, config, plugin_config, registry, is_optional=True
            ),
            ctx=ast.Load(),
        )

    raise NotImplementedError(f"Unknown input type {repr(graphql_type)}")


def generate_types(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: ObjectsPluginConfig,
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

    interface_map = {}

    for base in plugin_config.types_bases:
        registry.register_import(base)

    self_referential = set()

    for key, object_type in sorted_objects.items():

        additional_bases = get_additional_bases_for_type(
            object_type.name, config, registry
        )

        if plugin_config.skip_underscore and key.startswith("_"):
            continue

        if plugin_config.skip_double_underscore and key.startswith("__"):
            continue

        if isinstance(object_type, GraphQLObjectType):
            name = registry.generate_objecttype_classname(key)
        if isinstance(object_type, GraphQLInterfaceType):
            name = f"{registry.generate_interface_classname(key)}Base"

        for interface in object_type.interfaces:
            interface_map.setdefault(interface.name, []).append(name)
            additional_bases.append(
                ast.Name(
                    id=f"{registry.generate_interface_classname(interface.name)}Base",
                    ctx=ast.Load(),
                )
            )

        fields = (
            [ast.Expr(value=ast.Constant(value=object_type.description))]
            if object_type.description
            else []
        )

        for value_key, value in object_type.fields.items():

            if isinstance(value.type, GraphQLNonNull):
                if isinstance(value.type.of_type, GraphQLObjectType):
                    self_referential.add(
                        registry.generate_inputtype_classname(value.type.of_type.name)
                    )
                if isinstance(value.type.of_type, GraphQLInterfaceType):
                    self_referential.add(
                        registry.generate_interface_classname(value.type.of_type.name)
                    )

            if isinstance(value.type, GraphQLObjectType):
                self_referential.add(
                    registry.generate_inputtype_classname(value.type.name)
                )
            if isinstance(value.type, GraphQLInterfaceType):
                self_referential.add(
                    registry.generate_interface_classname(value.type.name)
                )

            field_name = registry.generate_node_name(value_key)

            if field_name != value_key:
                registry.register_import("pydantic.Field")
                assign = ast.AnnAssign(
                    target=ast.Name(field_name, ctx=ast.Store()),
                    annotation=generate_object_field_annotation(
                        value.type, config, plugin_config, registry, is_optional=True
                    ),
                    value=ast.Call(
                        func=ast.Name(id="Field", ctx=ast.Load()),
                        args=[],
                        keywords=[
                            ast.keyword(
                                arg="alias", value=ast.Constant(value=value_key)
                            )
                        ],
                    ),
                    simple=1,
                )
            else:
                assign = ast.AnnAssign(
                    target=ast.Name(value_key, ctx=ast.Store()),
                    annotation=generate_object_field_annotation(
                        value.type, config, plugin_config, registry, is_optional=True
                    ),
                    simple=1,
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

        registry.register_object_class(key, name)

        tree.append(
            ast.ClassDef(
                name,
                bases=additional_bases
                + [
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.types_bases
                ],
                decorator_list=[],
                keywords=[],
                body=fields,
            )
        )

    for interface, union_class_names in interface_map.items():
        registry.register_import("typing.Union")
        tree.append(
            ast.Assign(
                targets=(ast.Name(id=interface),),
                value=ast.Subscript(
                    value=ast.Name("Union", ctx=ast.Load()),
                    slice=ast.Tuple(
                        elts=[
                            ast.Name(id=clsname, ctx=ast.Load())
                            for clsname in union_class_names
                        ],
                        ctx=ast.Load(),
                    ),
                ),
            )
        )

    for input_name in self_referential:
        tree.append(
            ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(
                            id=input_name,
                            ctx=ast.Load(),
                        ),
                        attr="update_forward_refs",
                        ctx=ast.Load(),
                    ),
                    keywords=[],
                    args=[],
                )
            )
        )

    return tree


class ObjectsPlugin(Plugin):
    config: ObjectsPluginConfig = Field(default_factory=ObjectsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:

        return generate_types(client_schema, config, self.config, registry)
