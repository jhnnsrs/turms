import builtins
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    field_validator,
    validator,
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


class ConfigProxy(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str


class ImportableFunctionMixin(Protocol):

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate, handler(callable), field_name=handler.field_name
        )

    @classmethod
    def validate(cls, v, *info):
        if not callable(v):
            if not isinstance(v, str):
                raise TypeError("string required")
            assert "." in v, "You need to point to a module if its not a builtin type"
            v = import_string(v)

        assert callable(v)
        return v


class PythonType(str):
    """A string that represents a python type. Either a builtin type or a type from a module."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate, handler(str), field_name=handler.field_name
        )

    @classmethod
    def validate(cls, v, *info):
        if not isinstance(v, str):
            raise TypeError("string required")
        if v not in dir(builtins):
            assert "." in v, "You need to point to a module if its not a builtin type"
        return cls(v)


class GraphQLTypes(str, Enum):
    INPUT: str = "input"
    FRAGMENT: str = "fragment"
    OBJECT: str = "object"
    MUTATION = "mutation"
    QUERY = "query"
    SUBSCRIPTION = "subscription"
    DIRECTIVE: str = "directive"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@runtime_checkable
class LogFunction(Protocol):
    def __call__(self, message, level: LogLevel = LogLevel.INFO):
        pass


class FreezeConfig(BaseSettings):
    """Configuration for freezing the generated pydantic
    models

    This is useful for when you want to generate the models
    that are faux immutable and hashable by default. The configuration
    allows you to customize the way the models are frozen and specify
    which types (operation, fragment, input,...) should be frozen.

    """

    enabled: bool = Field(False, description="Enabling this, will freeze the schema")
    """Enabling this, will freeze the schema"""

    types: List[GraphQLTypes] = Field(
        [GraphQLTypes.INPUT, GraphQLTypes.FRAGMENT, GraphQLTypes.OBJECT],
        description="The types to freeze",
    )
    """The core types (Input, Fragment, Object, Operation) to freeze"""

    exclude: Optional[List[str]] = Field(
        None, description="List of types to exclude from freezing"
    )
    """List of types to exclude from freezing"""
    include: Optional[List[str]] = Field(
        None, description="List of types to include in freezing"
    )
    """The types to freeze"""
    exclude_fields: Optional[List[str]] = Field(
        [], description="List of fields to exclude from freezing"
    )
    include_fields: Optional[List[str]] = Field(
        [], description="List of fields to include in freezing"
    )
    convert_list_to_tuple: bool = Field(
        True, description="Convert GraphQL List to tuple (with varying length"
    )
    """Convert GraphQL List to tuple (with varying length)"""


ExtraOptions = Optional[Union[Literal["ignore"], Literal["allow"], Literal["forbid"]]]


class OptionsConfig(BaseSettings):
    """Configuration for freezing the generated pydantic
    models

    This is useful for when you want to generate the models
    that are faux immutable and hashable by default. The configuration
    allows you to customize the way the models are frozen and specify
    which types (operation, fragment, input,...) should be frozen.

    """

    enabled: bool = Field(False, description="Enabling this, will freeze the schema")
    """Enabling this, will freeze the schema"""
    extra: ExtraOptions = None
    """Extra options for pydantic"""
    allow_mutation: Optional[bool] = None
    """Allow mutation"""
    allow_population_by_field_name: Optional[bool] = None
    """Allow population by field name"""
    orm_mode: Optional[bool] = None
    """ORM mode"""
    use_enum_values: Optional[bool] = None
    """Use enum values"""

    validate_assignment: Optional[bool] = None
    """Validate assignment"""

    types: List[GraphQLTypes] = Field(
        [GraphQLTypes.INPUT, GraphQLTypes.FRAGMENT, GraphQLTypes.OBJECT],
        description="The types to freeze",
    )
    """The core types (Input, Fragment, Object, Operation) to enable this option"""

    exclude: Optional[List[str]] = Field(
        None, description="List of types to exclude from setting this option"
    )
    """List of types to exclude from setting this option"""
    include: Optional[List[str]] = Field(
        None, description="List of types to include in setting these options"
    )
    """The types to freeze"""


PydanticVersion = Literal["v1", "v2"]


class GeneratorConfig(BaseSettings):
    """Configuration for the generator

    This is the main generator configuration that allows you to
    customize the way the models are generated.

    You need to specify the documents that should be parsed
    and the scalars that should be used.

    """

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_prefix="TURMS_",
        extra="forbid",
    )
    pydantic_version: PydanticVersion = "v2"

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
    freeze: FreezeConfig = Field(
        default_factory=FreezeConfig,
        description="Configuration for freezing the generated models",
    )
    """Configuration for freezing the generated models: by default disabled"""

    options: OptionsConfig = Field(
        default_factory=OptionsConfig,
        description="Configuration for pydantic options",
    )
    """Configuration for pydantic options: by default disabled"""

    skip_forwards: bool = False
    """Skip generating automatic forwards reference for the generated models"""

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

    @field_validator("parsers", "plugins", "processors", "stylers")
    def validate_importable(cls, v):
        try:
            for parser in v:
                import_string(parser.type)
        except Exception as e:
            raise ValueError(f"Invalid import: {parser.type} {e}") from e

        return v
    

    @field_validator("additional_bases")
    def validate_additional_bases(cls, v):
        for key, value_list in v.items():
            for value in value_list:
                if not isinstance(value, str):
                    raise ValueError("string required")
                if value not in dir(builtins):
                    if "." not in value:
                        raise ValueError("You need to point to a module if its not a builtin type")
        return v



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

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_prefix="TURMS_GRAPHQL_",
        extra="allow",
    )

    schema_url: SchemaType = Field(alias="schema")
    """The schema url or path to the schema file"""
    documents: Optional[str] = None
    """The documents (operations,fragments) to parse"""
    extensions: Extensions
    """The extensions configuration for the project (here resides the turms configuration)"""


class GraphQLConfigMultiple(BaseSettings):
    """Configuration for multiple GraphQL projects

    This is the main configuration for multiple GraphQL projects. It is compliant with
    the graphql-config specification for multiple projec."""

    model_config: SettingsConfigDict = SettingsConfigDict(
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
