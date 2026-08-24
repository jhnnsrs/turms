import re
import textwrap
from dataclasses import dataclass
from graphql import (
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
    Undefined,
)
from turms.errors import GenerationError
from pydantic_settings import SettingsConfigDict
from turms.plugins.base import Plugin, PluginConfig, rename_deprecated_keys
import ast
from typing import Any, Dict, List, Optional
from turms.config import GeneratorConfig
from graphql import GraphQLSchema
from pydantic import Field, model_validator
from graphql.type.definition import (
    GraphQLEnumType,
)
from turms.referencer import create_reference_registry_from_documents
from turms.registry import ClassRegistry
from turms.utils import (
    annotate_field_metadata,
    compose_field_documentation,
    generate_alias_keywords,
    generate_pydantic_config,
    get_additional_bases_for_type,
    is_oneof_input_type,
    parse_documents,
)
from turms.config import GraphQLTypes


class InputsPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(
        extra="forbid", env_prefix="TURMS_PLUGINS_INPUTS_"
    )
    type: str = "turms.plugins.inputs.InputsPlugin"
    input_bases: List[str] = ["pydantic.BaseModel"]
    skip_underscore: bool = True
    skip_unreferenced: bool = True

    @model_validator(mode="before")
    @classmethod
    def _rename_deprecated(cls, values: Any) -> Any:
        return rename_deprecated_keys(values, {"inputtype_bases": "input_bases"})

    @model_validator(mode="before")
    @classmethod
    def _reject_removed_options(cls, values: Any) -> Any:
        if isinstance(values, dict) and "allow_population_by_field_name" in values:
            raise ValueError(
                "'allow_population_by_field_name' was never read by the inputs "
                "plugin and was removed in turms 2.0. Use the top-level "
                "'options.populate_by_name' instead."
            )
        return values


def generate_input_annotation(
    type: GraphQLScalarType | GraphQLEnumType | GraphQLInputObjectType,
    parent: str,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
    is_optional=True,
):
    if isinstance(type, GraphQLScalarType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_scalar(type.name),
            )

        return registry.reference_scalar(type.name)

    if isinstance(type, GraphQLInputObjectType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_inputtype(type.name, parent),
                ctx=ast.Load(),
            )
        return registry.reference_inputtype(type.name, parent)

    if isinstance(type, GraphQLEnumType):
        if is_optional:
            registry.register_import("typing.Optional")
            return ast.Subscript(
                value=ast.Name("Optional", ctx=ast.Load()),
                slice=registry.reference_enum(
                    type.name, parent, allow_forward=not config.force_plugin_order
                ),
                ctx=ast.Load(),
            )
        return registry.reference_enum(
            type.name, parent, allow_forward=not config.force_plugin_order
        )

    if isinstance(type, GraphQLNonNull):
        return generate_input_annotation(
            type.of_type, parent, config, plugin_config, registry, is_optional=False
        )

    if isinstance(type, GraphQLList):
        if (
            config.freeze.enabled
            and GraphQLTypes.INPUT in config.freeze.types
            and config.freeze.convert_list_to_tuple
        ):
            registry.register_import("typing.Tuple")

            def list_builder(x):
                return ast.Subscript(
                    value=ast.Name("Tuple", ctx=ast.Load()),
                    slice=ast.Tuple(elts=[x, ast.Constant(value=...)], ctx=ast.Load()),
                    ctx=ast.Load(),
                )

        else:
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
                    generate_input_annotation(
                        type.of_type,
                        parent,
                        config,
                        plugin_config,
                        registry,
                        is_optional=True,
                    )
                ),
                ctx=ast.Load(),
            )

        return list_builder(
            generate_input_annotation(
                type.of_type, parent, config, plugin_config, registry, is_optional=True
            )
        )

    raise NotImplementedError(f"Unknown input type {type}")


def generate_input_field_annotation(
    value_type: GraphQLInputType,
    parent: str,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
    omittable: bool,
):
    """Builds an input field's annotation. A NonNull field that is nonetheless
    omittable on the client (because it carries a schema default) defaults to
    ``None``, so its annotation must be wrapped in ``Optional[...]`` even though
    the GraphQL type is NonNull."""
    annotation = generate_input_annotation(
        value_type, parent, config, plugin_config, registry, is_optional=True
    )
    if omittable and isinstance(value_type, GraphQLNonNull):
        registry.register_import("typing.Optional")
        annotation = ast.Subscript(
            value=ast.Name(id="Optional", ctx=ast.Load()),
            slice=annotation,
            ctx=ast.Load(),
        )
    return annotation


def generate_input_field_value(
    field_name: str,
    value_key: str,
    omittable: bool,
    description: Optional[str],
    registry: ClassRegistry,
    config: GeneratorConfig,
):
    """Builds the AnnAssign value for an input field. Emits a ``Field(...)`` call
    carrying the alias, the ``None`` default (for omittable fields) and the GraphQL
    field description; falls back to a bare ``None``/required value when no
    ``Field`` metadata is needed.

    Never called for a discriminated-union tag field -- those are emitted by the
    ``discriminators`` loop in :func:`generate_input_type` and skipped here, which
    matters because pydantic rejects a split alias on a discriminator."""
    has_alias = field_name != value_key
    # A bare ``= None`` suffices for a plain optional field; only reach for a
    # ``Field(...)`` call when there is real metadata (an alias or a description)
    # to carry.
    if not has_alias and not description:
        return ast.Constant(value=None) if omittable else None

    keywords = []
    if has_alias:
        keywords.extend(
            generate_alias_keywords(field_name, value_key, config, registry)
        )
    if omittable:
        keywords.append(ast.keyword(arg="default", value=ast.Constant(value=None)))
    if description:
        keywords.append(
            ast.keyword(arg="description", value=ast.Constant(value=description))
        )

    registry.register_import("pydantic.Field")
    return ast.Call(
        func=ast.Name(id="Field", ctx=ast.Load()),
        args=[],
        keywords=keywords,
    )


@dataclass
class Discriminator:
    discriminator: str
    value: str


def generate_input_type(
    name: str,
    type: GraphQLInputType,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
    key: str,
    discriminators: Optional[List[Discriminator]] = None,
):
    additional_bases = get_additional_bases_for_type(type.name, config, registry)

    fields = (
        [ast.Expr(value=ast.Constant(value=type.description))]
        if type.description
        else [ast.Expr(value=ast.Constant(value="No documentation"))]
    )

    for discriminator in discriminators or []:
        registry.register_import("typing.Literal")
        registry.register_import("pydantic.Field")
        fields.append(
            ast.AnnAssign(
                target=ast.Name(discriminator.discriminator, ctx=ast.Store()),
                annotation=ast.Subscript(
                    value=ast.Name("Literal", ctx=ast.Load()),
                    slice=ast.Constant(value=discriminator.value),
                    ctx=ast.Load(),
                ),
                value=ast.Call(
                    func=ast.Name(id="Field", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="default", value=ast.Constant(value=discriminator.value)
                        )
                    ],
                ),
                simple=1,
            )
        )

    # A union member normally declares the discriminator as an ordinary field
    # (`kind: ElementKind! = LASER`), because it *is* an ordinary field on the
    # wire. The Literal emitted above is the same field, narrowed to the one
    # value this member answers to, so emitting it again here would shadow the
    # Literal with the open enum and leave pydantic unable to discriminate.
    #
    # The Literal is emitted under the *raw GraphQL* name, while the loop below
    # styles each field first, so a multi-word discriminator (`elementKind`)
    # would fail to match and be emitted twice. It also must never pick up an
    # alias: pydantic rejects a split alias on a discriminator ("Alias [...] is
    # not supported in a discriminated union"). Refuse rather than mis-emit.
    for _d in discriminators or []:
        _styled = registry.generate_node_name(_d.discriminator)
        if _styled != _d.discriminator:
            raise GenerationError(
                f"Discriminator '{_d.discriminator}' on '{type.name}' is styled to "
                f"'{_styled}', so it would need an alias -- which pydantic forbids "
                "on a discriminated-union tag field. Rename the field in the schema "
                "or use a styler that leaves it unchanged."
            )

    discriminator_names = {d.discriminator for d in discriminators or []}

    for value_key, value in type.fields.items():
        field_name = registry.generate_node_name(value_key)
        if field_name in discriminator_names:
            continue
        # A field is omittable (and thus optional, defaulting to None) when it is
        # nullable OR carries a schema default. For a default we no longer bake the
        # value: the field is omitted on serialization (exclude_unset) so the
        # server applies its own default.
        has_default = value.default_value is not Undefined
        # A null default carries no useful information; only mark non-null defaults.
        default_string = (
            str(value.default_value)
            if has_default and value.default_value is not None
            else None
        )
        omittable = has_default or not isinstance(value.type, GraphQLNonNull)

        annotation = generate_input_field_annotation(
            value.type, name, config, plugin_config, registry, omittable
        )
        # Record the GraphQL schema default (as a string) and deprecation as
        # Annotated markers.
        annotation = annotate_field_metadata(
            annotation,
            registry,
            default_value_ast=(
                ast.Constant(value=default_string) if default_string is not None else None
            ),
            deprecation_reason=value.deprecation_reason,
        )
        # The Field carries only the plain GraphQL description; the deprecation
        # reason and default are folded into the inline comment documentation
        # (unless opted out).
        documentation = compose_field_documentation(
            description=value.description,
            deprecation_reason=value.deprecation_reason,
            default_string=default_string,
            include_metadata=config.document_field_metadata,
        )

        assign = ast.AnnAssign(
            target=ast.Name(field_name, ctx=ast.Store()),
            annotation=annotation,
            value=generate_input_field_value(
                field_name, value_key, omittable, value.description, registry, config
            ),
            simple=1,
        )

        # Emit the inline comment only when it documents more than the plain
        # description already on the Field.
        if config.document_field_metadata and (
            value.deprecation_reason or default_string is not None
        ):
            fields += [assign, ast.Expr(value=ast.Constant(value=documentation))]
        else:
            fields += [assign]

    if discriminators:
        # The discriminator carries a default and is never explicitly set, so an
        # exclude_unset dump (the proxy contract) would drop it from the wire —
        # but the server needs it to discriminate. Mark it as set on every
        # construction so it always serializes.
        names = ", ".join(repr(d.discriminator) for d in discriminators)
        fields += ast.parse(
            "def model_post_init(self, context):\n"
            f"    self.__pydantic_fields_set__.update({{{names}}})\n"
        ).body

    return ast.ClassDef(
        name,
        bases=additional_bases
        + [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in plugin_config.input_bases
        ],
        decorator_list=[],
        keywords=[],
        body=fields
        + generate_pydantic_config(GraphQLTypes.INPUT, config, registry, typename=key),
    )


def validate_oneof_input_type(type: GraphQLInputObjectType):
    """Enforce the spec constraints on a ``@oneOf`` input: every field must be
    nullable and must not carry a default value."""
    for value_key, value in type.fields.items():
        if isinstance(value.type, GraphQLNonNull):
            raise GenerationError(
                f"@oneOf input type '{type.name}' has a non-nullable field "
                f"'{value_key}'. The spec requires all fields of a @oneOf input "
                "to be nullable."
            )
        if value.default_value is not Undefined:
            raise GenerationError(
                f"@oneOf input type '{type.name}' has a default value on field "
                f"'{value_key}'. The spec forbids defaults on @oneOf input fields."
            )


def get_oneof_member_map(
    type: GraphQLInputObjectType,
) -> Optional[Dict[str, GraphQLInputObjectType]]:
    """Field-name → member-type map when the ``@oneOf`` input follows the tagged
    input-union pattern: every field is a distinct, non-oneOf input object type.
    Returns ``None`` when the type cannot be modelled as a direct union of its
    member models (scalar/enum fields, duplicated member types, or oneOf
    members, whose tag could not be recovered from the value's type)."""
    members: Dict[str, GraphQLInputObjectType] = {}
    for value_key, value in type.fields.items():
        member = value.type
        if not isinstance(member, GraphQLInputObjectType) or is_oneof_input_type(
            member
        ):
            return None
        members[value_key] = member
    if len({member.name for member in members.values()}) != len(members):
        return None
    return members or None


def _pascal(name: str) -> str:
    return name[:1].upper() + name[1:]


def _snake(name: str) -> str:
    interim = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", interim).lower()


def generate_union_alias(alias_name: str, member_names: List[str], registry: ClassRegistry):
    if len(member_names) == 1:
        value = ast.Name(id=member_names[0], ctx=ast.Load())
    else:
        registry.register_import("typing.Union")
        value = ast.Subscript(
            value=ast.Name("Union", ctx=ast.Load()),
            slice=ast.Tuple(
                elts=[ast.Name(id=name, ctx=ast.Load()) for name in member_names],
                ctx=ast.Load(),
            ),
            ctx=ast.Load(),
        )
    return ast.Assign(
        targets=[ast.Name(id=alias_name, ctx=ast.Store())],
        value=value,
    )


def generate_oneof_wrapper_input(
    key: str,
    type: GraphQLInputObjectType,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
):
    """Generate a ``@oneOf`` input as a union of per-field wrapper classes, each
    carrying its single field as required. A wrapper serializes to the tagged
    wire form ``{fieldName: value}`` through the ordinary
    ``model_dump(by_alias=True, exclude_unset=True)`` proxy contract."""
    tree = []
    additional_bases = get_additional_bases_for_type(type.name, config, registry)
    member_names = []

    for value_key, value in type.fields.items():
        try:
            classname = registry.generate_inputtype(f"{type.name}{_pascal(value_key)}")
        except AssertionError as e:
            raise GenerationError(
                f"Cannot generate wrapper class for field '{value_key}' of @oneOf "
                f"input '{type.name}': the name '{type.name}{_pascal(value_key)}' "
                "is already taken by another type."
            ) from e
        member_names.append(classname)

        field_name = registry.generate_node_name(value_key)
        annotation = generate_input_annotation(
            value.type, classname, config, plugin_config, registry, is_optional=False
        )
        annotation = annotate_field_metadata(
            annotation, registry, deprecation_reason=value.deprecation_reason
        )
        docstring = (
            value.description
            or f"'{value_key}' variant of the @oneOf input '{type.name}'"
        )

        tree.append(
            ast.ClassDef(
                classname,
                bases=additional_bases
                + [
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.input_bases
                ],
                decorator_list=[],
                keywords=[],
                body=[
                    ast.Expr(value=ast.Constant(value=docstring)),
                    ast.AnnAssign(
                        target=ast.Name(field_name, ctx=ast.Store()),
                        annotation=annotation,
                        value=generate_input_field_value(
                            field_name, value_key, False, value.description, registry, config
                        ),
                        simple=1,
                    ),
                ]
                + generate_pydantic_config(
                    GraphQLTypes.INPUT, config, registry, typename=key
                ),
            )
        )

    alias_name = registry.generate_inputtype(key)
    tree.append(generate_union_alias(alias_name, member_names, registry))
    return tree


def generate_oneof_direct_union(
    key: str,
    type: GraphQLInputObjectType,
    members: Dict[str, GraphQLInputObjectType],
    registry: ClassRegistry,
):
    """Generate a ``@oneOf`` input following the tagged input-union pattern as a
    direct union of the member models, with a ``WrapSerializer`` restoring the
    ``{fieldName: memberDict}`` wire form. Must be emitted after all member
    classes (the tag dict references them at module level)."""
    alias_name = registry.generate_inputtype(key)
    serializer_name = f"_serialize_{_snake(alias_name)}"

    member_classnames = {
        value_key: registry.get_inputtype_class(member.name)
        for value_key, member in members.items()
    }
    tags = ", ".join(
        f"{classname}: {value_key!r}"
        for value_key, classname in member_classnames.items()
    )
    union = ", ".join(dict.fromkeys(member_classnames.values()))
    if len(member_classnames) > 1:
        registry.register_import("typing.Union")
        union = f"Union[{union}]"

    registry.register_import("typing.Annotated")
    registry.register_import("pydantic.WrapSerializer")

    source = textwrap.dedent(
        f'''
        def {serializer_name}(value, handler):
            """Wire serializer for the @oneOf input '{type.name}': wraps the
            serialized member under its field tag."""
            tags = {{{tags}}}
            tag = tags.get(type(value))
            if tag is None:
                for member_class, member_tag in tags.items():
                    if isinstance(value, member_class):
                        tag = member_tag
                        break
            if tag is None:
                raise ValueError(
                    f"{{type(value)!r}} is not a member of the @oneOf input '{type.name}'"
                )
            return {{tag: handler(value)}}


        {alias_name} = Annotated[{union}, WrapSerializer({serializer_name})]
        '''
    )
    return ast.parse(source).body


def generate_inputs(
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: InputsPluginConfig,
    registry: ClassRegistry,
):
    tree = []

    inputobjects_type = {
        key: value
        for key, value in client_schema.type_map.items()
        if isinstance(value, GraphQLInputObjectType)
    }

    if plugin_config.skip_unreferenced and config.documents:
        ref_registry = create_reference_registry_from_documents(
            client_schema, parse_documents(client_schema, config.documents, config)
        )
    else:
        ref_registry = None

    for base in plugin_config.input_bases:
        registry.register_import(base)

    union_input_types = {}
    union_type_discriminators = {}
    # Member types generated by the unionElementOf pre-pass; the main loop must
    # not generate them a second time.
    union_member_types = set()

    for type_key, type in inputobjects_type.items():
        directives = type.ast_node.directives if type.ast_node else []
        # unionElementOf is repeatable: a member may belong to several unions.
        memberships = []
        for directive in directives:
            if directive.name.value != "unionElementOf":
                continue
            args = {arg.name.value: arg.value.value for arg in directive.arguments}
            union_type = args.get("union")
            discriminator = args.get("discriminator")
            member_key = args.get("key")
            if union_type is None or discriminator is None or member_key is None:
                raise GenerationError(
                    f"@unionElementOf on '{type.name}' needs 'union', "
                    "'discriminator' and 'key' arguments."
                )
            # Skip memberships of unions that won't be generated.
            if ref_registry is not None and union_type not in ref_registry.inputs:
                continue
            if union_type in union_type_discriminators:
                if union_type_discriminators[union_type] != discriminator:
                    raise GenerationError(
                        f"Discriminator mismatch for union '{union_type}': expected "
                        f"'{union_type_discriminators[union_type]}', got "
                        f"'{discriminator}' on '{type.name}'."
                    )
            else:
                union_type_discriminators[union_type] = discriminator
            memberships.append((union_type, discriminator, member_key))

        if not memberships:
            continue

        # One Literal field per distinct discriminator name; all unions sharing
        # a discriminator name must agree on this member's key.
        discriminators: Dict[str, Discriminator] = {}
        for union_type, discriminator, member_key in memberships:
            existing = discriminators.get(discriminator)
            if existing is not None and existing.value != member_key:
                raise GenerationError(
                    f"'{type.name}' uses discriminator '{discriminator}' with "
                    f"conflicting keys '{existing.value}' and '{member_key}'."
                )
            discriminators[discriminator] = Discriminator(
                discriminator=discriminator, value=member_key
            )

        name = registry.generate_inputtype(type.name)
        union_member_types.add(type_key)
        for union_type, _, _ in memberships:
            union_input_types.setdefault(union_type, [])
            if name not in union_input_types[union_type]:
                union_input_types[union_type].append(name)
        tree.append(
            generate_input_type(
                name,
                type,
                config,
                plugin_config,
                registry,
                type.name,
                list(discriminators.values()),
            )
        )

    # Direct oneOf unions reference their member classes at module level (tag
    # dict + Union), so their emission is deferred until after every input
    # class has been generated.
    deferred_oneof_unions = []

    for key, type in inputobjects_type.items():
        if key in union_member_types:
            continue

        if ref_registry and key not in ref_registry.inputs:
            continue

        if plugin_config.skip_underscore and key.startswith("_"):  # pragma: no cover
            continue

        if is_oneof_input_type(type):
            validate_oneof_input_type(type)
            members = get_oneof_member_map(type)
            if members is not None and any(
                (ref_registry and member.name not in ref_registry.inputs)
                or (plugin_config.skip_underscore and member.name.startswith("_"))
                for member in members.values()
            ):
                # A member will not be generated into this module, so the direct
                # union cannot reference it; fall back to wrapper classes.
                members = None
            if members is not None:
                deferred_oneof_unions.append((key, type, members))
            else:
                tree.extend(
                    generate_oneof_wrapper_input(
                        key, type, config, plugin_config, registry
                    )
                )
            continue

        if type.name in union_input_types:
            registry.register_import("typing.Union")
            registry.register_import("typing.Annotated")
            registry.register_import("pydantic.Field")
            union_slice = ast.Tuple(
                elts=[
                    ast.Name(id=clsname, ctx=ast.Load())
                    for clsname in union_input_types[type.name]
                ],
                ctx=ast.Load(),
            )

            slice = ast.Tuple(
                elts=[
                    ast.Subscript(
                        value=ast.Name("Union", ctx=ast.Load()),
                        slice=union_slice,
                        ctx=ast.Load(),
                    ),
                    ast.Call(
                        func=ast.Name(id="Field", ctx=ast.Load()),
                        args=[],
                        keywords=[
                            ast.keyword(
                                arg="discriminator",
                                value=ast.Constant(
                                    union_type_discriminators[type.name]
                                ),
                            )
                        ],
                    ),
                ],
                ctx=ast.Load(),
            )

            tree.append(
                ast.Assign(
                    targets=[
                        ast.Name(
                            id=registry.generate_inputtype(type.name),
                            ctx=ast.Store(),
                        )
                    ],
                    value=ast.Subscript(
                        value=ast.Name("Annotated", ctx=ast.Load()),
                        slice=slice,
                        ctx=ast.Load(),
                    ),
                )
            )

            continue

        additional_bases = get_additional_bases_for_type(type.name, config, registry)
        name = registry.generate_inputtype(key)
        fields = (
            [ast.Expr(value=ast.Constant(value=type.description))]
            if type.description
            else [ast.Expr(value=ast.Constant(value="No documentation"))]
        )

        for value_key, value in type.fields.items():
            field_name = registry.generate_node_name(value_key)
            # Omittable (optional, default None) when nullable OR carrying a schema
            # default; defaults are deferred to the server via exclude_unset.
            has_default = value.default_value is not Undefined
            # A null default carries no useful information; only mark non-null defaults.
            default_string = (
                str(value.default_value)
                if has_default and value.default_value is not None
                else None
            )
            omittable = has_default or not isinstance(value.type, GraphQLNonNull)

            annotation = generate_input_field_annotation(
                value.type, name, config, plugin_config, registry, omittable
            )
            # Record the GraphQL schema default (as a string) and deprecation as
            # Annotated markers.
            annotation = annotate_field_metadata(
                annotation,
                registry,
                default_value_ast=(
                    ast.Constant(value=default_string) if default_string is not None else None
                ),
                deprecation_reason=value.deprecation_reason,
            )
            documentation = compose_field_documentation(
                description=value.description,
                deprecation_reason=value.deprecation_reason,
                default_string=default_string,
                include_metadata=config.document_field_metadata,
            )

            assign = ast.AnnAssign(
                target=ast.Name(field_name, ctx=ast.Store()),
                annotation=annotation,
                value=generate_input_field_value(
                    field_name, value_key, omittable, value.description, registry, config
                ),
                simple=1,
            )

            # Emit the inline comment only when it documents more than the plain
            # description already on the Field.
            if config.document_field_metadata and (
                value.deprecation_reason or default_string is not None
            ):
                fields += [
                    assign,
                    ast.Expr(value=ast.Constant(value=documentation)),
                ]
            else:
                fields += [assign]

        tree.append(
            ast.ClassDef(
                name,
                bases=additional_bases
                + [
                    ast.Name(id=base.split(".")[-1], ctx=ast.Load())
                    for base in plugin_config.input_bases
                ],
                decorator_list=[],
                keywords=[],
                body=fields
                + generate_pydantic_config(
                    GraphQLTypes.INPUT, config, registry, typename=key
                ),
            )
        )

    for key, type, members in deferred_oneof_unions:
        tree.extend(generate_oneof_direct_union(key, type, members, registry))

    return tree


class InputsPlugin(Plugin):
    """Generate pydantic Models for GraphQL inputs

    This plugin generates pydantic models for all GraphQL inputtypes in
    your schema. It will generate a model for each inputtype in your schema.

    """

    config: InputsPluginConfig = Field(default_factory=InputsPluginConfig)

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        for base in self.config.input_bases:
            registry.register_import(base)

        return generate_inputs(client_schema, config, self.config, registry)
