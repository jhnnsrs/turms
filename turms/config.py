import builtins
from graphql import ASTValidationRule
from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    field_validator,
    model_validator,
    ConfigDict,
)
from pydantic_core import core_schema
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
    Protocol,
    Literal,
    runtime_checkable,
)
from turms.helpers import import_string
from enum import Enum
from .rules import specified_rules_map


class ConfigProxy(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str


class ImportableFunctionMixin(Protocol):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(
            cls.validate, handler(Any)
        )

    @classmethod
    def validate(cls, value: Union[str, Callable[[Any], Any]]):
        if not callable(value):
            if not isinstance(value, str):  # type: ignore
                raise TypeError("string required")
            assert "." in value, (
                "You need to point to a module if its not a builtin type"
            )
            value = import_string(value)

        return value


class PythonType(str):
    """A string that represents a python type. Either a builtin type or a type from a module."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(cls.validate, handler(str))

    @classmethod
    def validate(cls, v: str):
        if v not in dir(builtins):
            assert "." in v, "You need to point to a module if its not a builtin type"
        return cls(v)


class GraphQLTypes(str, Enum):
    INPUT = "input"
    FRAGMENT = "fragment"
    OBJECT = "object"
    MUTATION = "mutation"
    QUERY = "query"
    SUBSCRIPTION = "subscription"
    DIRECTIVE = "directive"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@runtime_checkable
class LogFunction(Protocol):
    def __call__(
        self,
        message: str,
        level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    ) -> None:
        pass


class FreezeConfig(BaseModel):
    """Configuration for freezing the generated pydantic
    models

    This is useful for when you want to generate the models
    that are faux immutable and hashable by default. The configuration
    allows you to customize the way the models are frozen and specify
    which types (operation, fragment, input,...) should be frozen.

    """

    enabled: bool = Field(
        default=False, description="Enabling this, will freeze the schema"
    )
    """Enabling this, will freeze the schema"""

    types: List[GraphQLTypes] = Field(
        default=[GraphQLTypes.INPUT, GraphQLTypes.FRAGMENT, GraphQLTypes.OBJECT],
        description="The types to freeze",
    )
    """The core types (Input, Fragment, Object, Operation) to freeze"""

    exclude: Optional[List[str]] = Field(
        default=None, description="List of types to exclude from freezing"
    )
    """List of types to exclude from freezing"""
    include: Optional[List[str]] = Field(
        default=None, description="List of types to include in freezing"
    )
    """The types to freeze"""
    convert_list_to_tuple: bool = Field(
        default=True, description="Convert GraphQL List to tuple (with varying length"
    )
    """Convert GraphQL List to tuple (with varying length)"""


ExtraOptions = Optional[Literal["ignore", "allow", "forbid"]]

AliasMode = Literal["single", "split"]
"""How a field whose python name differs from its GraphQL name carries that name.

- ``single`` (default): one ``Field(alias="graphQLName")``. pydantic uses it for
  both validation and serialization. Type checkers synthesize ``__init__`` from
  the alias and do **not** read ``populate_by_name``, so the python (snake_case)
  spelling is reported as an unknown argument even though it works at runtime.
- ``split``: ``validation_alias=AliasChoices("python_name", "graphQLName")`` plus
  ``serialization_alias="graphQLName"``. Both spellings still validate, the wire
  format is unchanged, and type checkers now see the python name -- because no
  ``alias=`` specifier is present, they fall back to the field name.
"""


class OptionsConfig(BaseModel):
    """Configuration for freezing the generated pydantic
    models

    This is useful for when you want to generate the models
    that are faux immutable and hashable by default. The configuration
    allows you to customize the way the models are frozen and specify
    which types (operation, fragment, input,...) should be frozen.

    """

    enabled: bool = Field(
        default=False, description="Enabling this, will freeze the schema"
    )
    """Enabling this, will freeze the schema"""
    extra: ExtraOptions = None
    """Extra options for pydantic"""
    populate_by_name: Optional[bool] = Field(
        default=None,
        validation_alias=AliasChoices(
            "populate_by_name", "allow_population_by_field_name"
        ),
    )
    """Emit ``populate_by_name`` on the generated models.

    ``allow_population_by_field_name`` -- the pydantic v1 spelling of this key --
    is still accepted as a deprecated alias."""
    from_attributes: Optional[bool] = None
    """Let the generated models validate from arbitrary class instances"""
    use_enum_values: Optional[bool] = None
    """Use enum values"""

    validate_assignment: Optional[bool] = None
    """Validate assignment"""

    alias_mode: AliasMode = "single"
    """Whether aliases are emitted as one ``alias=`` or split into
    ``validation_alias``/``serialization_alias``. See :data:`AliasMode`.

    Applies to input types and operation ``Arguments`` only -- the types a caller
    constructs. Output types (fragments, objects, operation results) are parsed
    from the wire and keep a single ``alias=``.

    Deliberately independent of ``enabled``, ``types``, ``include`` and
    ``exclude``: those select which models receive a generated ``model_config``,
    whereas ``alias_mode`` chooses how an individual ``Field(...)`` specifier
    spells its alias. The two are unrelated concerns, and gating the field
    specifier on ``types`` would be ambiguous anyway -- ``Arguments`` is an
    OPERATION-scoped model whose aliasing must follow the INPUT policy, because
    the generated functions construct it the same way a caller constructs an
    input."""

    @model_validator(mode="before")
    @classmethod
    def _reject_pydantic_v1_options(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "orm_mode" in values:
                raise ValueError(
                    "'orm_mode' is a pydantic v1 config key and was removed in "
                    "turms 2.0. Use 'from_attributes' instead."
                )
            if "allow_mutation" in values:
                raise ValueError(
                    "'allow_mutation' is a pydantic v1 config key and was "
                    "removed in turms 2.0. Use the 'freeze' section to generate "
                    "immutable models."
                )
        return values

    types: List[GraphQLTypes] = Field(
        default=[GraphQLTypes.INPUT, GraphQLTypes.FRAGMENT, GraphQLTypes.OBJECT],
        description="The types to freeze",
    )
    """The core types (Input, Fragment, Object, Operation) to enable this option"""

    exclude: Optional[List[str]] = Field(
        default=None, description="List of types to exclude from setting this option"
    )
    """List of types to exclude from setting this option"""
    include: Optional[List[str]] = Field(
        default=None, description="List of types to include in setting these options"
    )
    """The types to freeze"""


PythonVersion = Literal["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
"""A python version the generated code can be targeted at."""

TypeAnnotationStyle = Literal["legacy", "modern", "auto"]
"""How type annotations are spelled in the generated code.

- ``auto``: pick the most modern spelling that ``min_python_version`` supports (the default)
- ``modern``: always ``list[X] | None`` (PEP 585 builtin generics + PEP 604 unions)
- ``legacy``: always ``typing.Optional[typing.List[X]]``, whatever the target version
"""

#: The python version each modern-annotation feature became available in.
BUILTIN_GENERICS_SINCE = (3, 9)  # PEP 585: list[int] instead of typing.List[int]
UNION_OPERATOR_SINCE = (3, 10)  # PEP 604: int | None instead of typing.Optional[int]


def parse_python_version(version: str) -> tuple:
    """Turns a ``"3.10"`` style version string into a comparable tuple."""
    return tuple(int(part) for part in version.split("."))



#: Components removed in turms 2.0, mapped to the error a config still naming one gets.
#: Without this they would fail as an opaque "Invalid import".
REMOVED_COMPONENTS = {
    "turms.parsers.polyfill.PolyfillParser": (
        "'turms.parsers.polyfill.PolyfillParser' was removed in turms 2.0. It only "
        "backported 'Literal' to typing_extensions for a python 3.7 target, and "
        "pydantic v2 -- the only target turms generates for -- has never supported "
        "python 3.7. Drop the parser from your configuration."
    ),
    "turms.parsers.polyfill.PolyfillPlugin": (
        "'turms.parsers.polyfill.PolyfillPlugin' was removed in turms 2.0. Drop the "
        "parser from your configuration."
    ),
}


class GeneratorConfig(BaseSettings):
    """Configuration for the generator

    This is the main generator configuration that allows you to
    customize the way the models are generated.

    You need to specify the documents that should be parsed
    and the scalars that should be used.

    """

    model_config = SettingsConfigDict(
        env_prefix="TURMS_",
        extra="forbid",
    )
    @model_validator(mode="before")
    @classmethod
    def _drop_pydantic_version(cls, values: Any) -> Any:
        """``pydantic_version`` is a dead key: turms only targets pydantic v2.

        Configurations saying ``pydantic_version: v2`` keep loading -- the key
        is accepted and discarded, so it carries forward into neither
        ``model_dump()`` nor ``model_json_schema()`` nor a dumped
        ``project.json``. Asking for v1 is an error.
        """
        if isinstance(values, dict) and "pydantic_version" in values:
            if values.pop("pydantic_version") in ("v1", "1", 1):
                raise ValueError(
                    "pydantic v1 targets were removed in turms 2.0. The generated "
                    "code now always targets pydantic v2 — drop the "
                    "'pydantic_version' key from your configuration and upgrade "
                    "the consuming project to pydantic>=2."
                )
        return values

    domain: Optional[str] = None
    """The domain of the GraphQL API ( will be set as a config variable)"""
    out_dir: str = "api"
    """The output directory for the generated models"""
    dump_configuration: bool = False
    configuration_name: str = "project.json"
    dump_schema: bool = False
    schema_name: str = "schema.graphql"
    generated_name: str = "schema.py"
    """ The name of the generated file within the output directory"""
    documents: Optional[str] = None
    """The documents to parse. Setting this will overwrite the documents in the graphql config"""
    verbose: bool = False
    """Enable verbose logging"""

    exit_on_error: bool = True
    """Will cause a sys.exit(1) if an error occurs"""

    allow_introspection: bool = True
    """Allow introspection queries"""

    object_bases: List[str] = ["pydantic.BaseModel"]
    """The base classes for the generated objects. This is useful if you want to change the base class from BaseModel to something else"""

    interface_bases: Optional[List[str]] = None
    """List of base classes for interfaces"""
    always_resolve_interfaces: bool = True
    """Always resolve interfaces to concrete types"""
    exclude_typenames: bool = False
    """Exclude __typename from generated models when calling dict or json"""

    scalar_definitions: Dict[str, PythonType] = Field(
        default_factory=dict,
        description="Additional config for mapping scalars to python types (e.g. ID: str). Can use dotted paths to import types from other modules.",
    )
    """Additional config for mapping scalars to python types (e.g. ID: str). Can use dotted paths to import types from other modules."""

    coercible_scalars: Dict[str, PythonType] = Field(
        default_factory=dict,
        description="Global map of scalar names to a coercible python type used in generated function/factory parameters (e.g. ID: pydantic.UUID4). Plugins (funcs, input_funcs) merge their own coercible_scalars on top of this, overriding per-scalar.",
    )
    """Global coercible scalar map. Plugins merge their own coercible_scalars on top (plugin entries override)."""

    coercible_inputs: Dict[str, PythonType] = Field(
        default_factory=dict,
        description="Global map of input type names to an additional python type accepted in generated function/factory parameters. The annotation is generated as a Union of the input model and the given type (e.g. AxisInput: str -> Union[AxisInput, str]); the input model performs the coercion (e.g. via a before-validator). Plugins (funcs, input_funcs) merge their own coercible_inputs on top of this, overriding per-type.",
    )
    """Global coercible input-type map (input model unioned with the given type). Plugins merge their own coercible_inputs on top (plugin entries override)."""

    graphql_default_class: Optional[PythonType] = Field(
        default=None,
        description="Importable class used as the Annotated marker carrying a field's GraphQL schema default value. If unset, a GraphQLDefault marker is generated into the output module.",
    )
    """Importable class for the GraphQLDefault Annotated marker. If unset, it is generated into the output module."""

    deprecated_class: Optional[PythonType] = Field(
        default=None,
        description="Importable class used as the Annotated marker for deprecated fields. If unset, a Deprecated marker is generated into the output module.",
    )
    """Importable class for the Deprecated Annotated marker. If unset, it is generated into the output module."""

    document_field_metadata: bool = Field(
        default=True,
        description="Fold the GraphQL deprecation reason and default value into the human-readable field documentation (description / comment), in addition to the Annotated markers. Set False to opt out and keep only the plain description.",
    )
    """Include the deprecation warning and default value in the field documentation. Opt out by setting False."""

    unset_type_class: Optional[PythonType] = Field(
        default=None,
        description="Importable class used as the UNSET sentinel TYPE (the type referenced in Union[..., UnsetType] parameter annotations). If unset, an UnsetType class is generated into the output module. Must be set together with unset_instance.",
    )
    """Importable class for the UNSET sentinel type. If unset, it is generated. Set together with unset_instance."""

    unset_instance: Optional[PythonType] = Field(
        default=None,
        description="Importable UNSET sentinel INSTANCE (used as the omitted-argument default and in identity checks). If unset, an UNSET instance is generated into the output module. Must be set together with unset_type_class.",
    )
    """Importable UNSET sentinel instance. If unset, it is generated. Set together with unset_type_class."""
    freeze: FreezeConfig = Field(
        default_factory=lambda: FreezeConfig(),
        description="Configuration for freezing the generated models",
    )
    """Configuration for freezing the generated models: by default disabled"""

    create_catchall: bool = Field(
        default=True,
        description="Create a catchall for interface implemtations. This will allow to use a catchall type to retrieve interface implementations that might exist on the server but are not defined in the schema that is used to generate the models.",
    )

    options: OptionsConfig = Field(
        default_factory=OptionsConfig,
        description="Configuration for pydantic options",
    )
    """Configuration for pydantic options: by default disabled"""

    skip_forwards: bool = False
    """Skip generating automatic forwards reference for the generated models"""

    min_python_version: PythonVersion = Field(
        default="3.10",
        description="The oldest python version the generated code has to run on. Drives the annotation spelling while type_annotation_style is 'auto'.",
    )
    """The oldest python version the generated code has to run on (drives `type_annotation_style: auto`)"""

    type_annotation_style: TypeAnnotationStyle = Field(
        default="auto",
        description="How type annotations are spelled: 'auto' picks the most modern spelling min_python_version supports, 'modern' always uses PEP 585 builtin generics and PEP 604 unions (list[X] | None), 'legacy' always uses typing.Optional/typing.List.",
    )
    """How type annotations are spelled: auto (derived from min_python_version), modern, or legacy"""

    additional_bases: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Additional bases for the generated models as map of GraphQL Type to importable base class (e.g. module.package.Class)",
    )
    "Additional bases for the generated models as map of GraphQL Type to importable base class (e.g. module.package.Class)"
    additional_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional config for the generated models as map of GraphQL Type to config attributes",
    )
    "Additional config for the generated models as map of GraphQL Type to config attributes"

    force_plugin_order: bool = True
    "Should the plugins be forced to run in the order they are defined"

    omited_document_rules: List[str] = Field(
        default_factory=list,
        description="List of rules to omit from the document validation. This is useful if you want to skip certain rules that are not relevant for your use case.",
    )
    "List of rules to omit from the document validation."

    parsers: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of parsers to use. Parsers are used to parse the generated AST and translate it before it is converted to python code",
    )
    "List of parsers to use. Parsers are used to parse the generated AST and translate it before it is converted to python code"

    plugins: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of plugins to use. Plugins are used to generated the python ast from the graphql documents, objects, etc.",
    )
    "List of plugins to use. Plugins are used to generated the python ast from the graphql documents, objects, etc."
    processors: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of processors to use. Processor are used to enforce specific styles on the generated python code",
    )
    "List of processors to use. Processor are used to enforce specific styles on the generated python code"
    stylers: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of stylers to use. Style are used to enforce specific styles on the generaded class or fieldnames. ",
    )
    "List of stylers to use. Style are used to enforce specific styles on the generaded class or fieldnames. "

    @property
    def _target_python_version(self) -> tuple:
        """The python version the annotation style is resolved against."""
        if self.type_annotation_style == "modern":
            # An explicit `modern` opts into every modern spelling turms knows,
            # regardless of the declared floor.
            return UNION_OPERATOR_SINCE
        return parse_python_version(self.min_python_version)

    @property
    def use_builtin_generics(self) -> bool:
        """Emit PEP 585 builtin generics (``list[X]``) instead of ``typing.List[X]``."""
        if self.type_annotation_style == "legacy":
            return False
        return self._target_python_version >= BUILTIN_GENERICS_SINCE

    @property
    def use_union_operator(self) -> bool:
        """Emit PEP 604 unions (``X | None``) instead of ``typing.Optional[X]``."""
        if self.type_annotation_style == "legacy":
            return False
        return self._target_python_version >= UNION_OPERATOR_SINCE

    @model_validator(mode="after")
    def validate_unset_override(self):
        """The UNSET sentinel type and instance must be overridden together (the
        generated ``UNSET = UnsetType()`` bundle is emitted only when neither is
        overridden)."""
        if (self.unset_type_class is None) != (self.unset_instance is None):
            raise ValueError(
                "unset_type_class and unset_instance must be set together (or neither)."
            )
        return self

    @field_validator("parsers", "plugins", "processors", "stylers", mode="after")
    def validate_importable(cls, v: List[ConfigProxy]) -> List[ConfigProxy]:
        """Validate that the importable is a valid importable function or class"""

        for parser in v:
            if parser.type in REMOVED_COMPONENTS:
                raise ValueError(REMOVED_COMPONENTS[parser.type])
            try:
                import_string(parser.type)
            except Exception as e:
                raise ValueError(f"Invalid import: {parser.type} {e}") from e

        return v

    @field_validator("omited_document_rules", mode="after")
    def validate_omited_document_rules(cls, v: List[str]) -> List[str]:
        """Validate that the omited document rules are valid"""
        for rule in v:
            if rule not in specified_rules_map:
                raise ValueError(
                    f"Invalid rule: {rule}. Available rules: {specified_rules_map.keys()}"
                )
        return v

    @field_validator(
        "additional_bases",
        mode="after",
    )
    def validate_additional_bases(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Validate that the additional bases are valid importable functions or classes"""
        for key, value_list in v.items():
            for value in value_list:
                if not isinstance(value, str):  # type: ignore
                    raise ValueError("string required")
                if value not in dir(builtins):
                    if "." not in value:
                        raise ValueError(
                            "You need to point to a module if its not a builtin type"
                        )
        return v

    def get_document_rules(self) -> List[ASTValidationRule]:
        """Get the schema rules to use for validation"""
        rules = []
        for key, rule in specified_rules_map.items():
            if key in self.omited_document_rules:
                continue
            rules.append(rule)
        return rules


class Extensions(BaseModel):
    """Wrapping class to be able to extract the tums configuraiton"""

    turms: GeneratorConfig
    "The turms configuration"


class AdvancedSchemaField(BaseModel):
    headers: Dict[str, str]


SchemaField = Union[AnyHttpUrl, str, Dict[str, AdvancedSchemaField]]
SchemaType = Union[SchemaField, List[SchemaField]]


class GraphQLProject(BaseSettings):
    """Configuration for the GraphQL project

    This is the main configuration for one GraphQL project. It is compliant with
    the graphql-config specification. And allows you to specify the schema and
    the documents that should be parsed.

    Turm will use the schema and documents to generate the python models, according
    to the generator configuration under extensions.turms
    """

    model_config = SettingsConfigDict(
        env_prefix="TURMS_GRAPHQL_",
        extra="allow",
    )

    schema_url: SchemaType = Field(
        validation_alias=AliasChoices("schema", "schema_url"),
        serialization_alias="schema",
    )
    """The schema url or path to the schema file"""
    documents: Optional[str] = None
    """The documents (operations,fragments) to parse"""
    extensions: Extensions
    """The extensions configuration for the project (here resides the turms configuration)"""


class GraphQLConfigMultiple(BaseModel):
    """Configuration for multiple GraphQL projects

    This is the main configuration for multiple GraphQL projects. It is compliant with
    the graphql-config specification for multiple projec."""

    model_config = ConfigDict(
        extra="allow",
    )

    projects: Dict[str, GraphQLProject]
    """ The projects that should be parsed. The key is the name of the project and the value is the graphql project"""


class GraphQLConfigSingle(GraphQLProject):
    """Configuration for a single GraphQL project

    This is the main configuration for a single GraphQL project. It is compliant with
    the graphql-config specification for a single project.
    """

    model_config: SettingsConfigDict = SettingsConfigDict(
        extra="allow",
    )
