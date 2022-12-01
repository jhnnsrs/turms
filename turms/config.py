import builtins
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Field, validator
from typing import Any, Dict, List, Optional, Union
from turms.helpers import import_string
from enum import Enum


class ConfigProxy(BaseModel):
    type: str

    class Config:
        extra = "allow"


class PythonType(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
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


class FreezeConfig(BaseSettings):
    """Configuration for freezing the generated pydantic
    models

    This is useful for when you want to generate the models
    that are faux immutable and hashable by default. The configuration
    allows you to customize the way the models are frozen and specify
    which types (operation, fragment, input,...) should be frozen.

    """

    enabled: bool = Field(False, description="Enabling this, will freeze the schema")

    types: List[GraphQLTypes] = Field(
        [GraphQLTypes.INPUT, GraphQLTypes.FRAGMENT, GraphQLTypes.OBJECT],
        description="The types to freeze",
    )
    exclude: Optional[List[str]] = Field(
        description="List of types to exclude from freezing"
    )
    include: Optional[List[str]] = Field(
        description="List of types to include in freezing"
    )
    exclude_fields: Optional[List[str]] = Field(
        [], description="List of fields to exclude from freezing"
    )
    include_fields: Optional[List[str]] = Field(
        [], description="List of fields to include in freezing"
    )
    convert_list_to_tuple: bool = Field(
        True, description="Convert GraphQL List to tuple (with varying length"
    )


class GeneratorConfig(BaseSettings):
    """Configuration for the generator

    This is the main generator configuration that allows you to
    customize the way the models are generated.

    You need to specify the documents that should be parsed
    and the scalars that should be used.

    """

    domain: Optional[str] = None
    out_dir: str = "api"
    generated_name: str = "schema.py"
    documents: Optional[str]
    verbose: bool = False

    object_bases: List[str] = ["pydantic.BaseModel"]

    interface_bases: Optional[List[str]] = None
    always_resolve_interfaces: bool = True

    scalar_definitions: Dict[str, PythonType] = Field(
        default_factory=dict,
        description="Additional config for mapping scalars to python types (e.g. ID: str). Can use dotted paths to import types from other modules.",
    )
    freeze: FreezeConfig = Field(
        default_factory=FreezeConfig,
        description="Configuration for freezing the generated models",
    )

    additional_bases: Dict[str, Dict[str, PythonType]] = Field(
        default_factory=dict,
        description="Additional config for the generated models as map of GraphQL Type to importable base class (e.g. module.package.Class)",
    )
    additional_config: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional config for the generated models as map of GraphQL Type to config attributes",
    )
    force_plugin_order: bool = True

    parsers: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of parsers to use. Parsers are used to parse the generated AST and translate it before it is converted to python code",
    )

    plugins: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of plugins to use. Plugins are used to generated the python ast from the graphql documents, objects, etc.",
    )
    processors: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of processors to use. Processor are used to enforce specific styles on the generated python code",
    )
    stylers: List[ConfigProxy] = Field(
        default_factory=list,
        description="List of stylers to use. Style are used to enforce specific styles on the generaded class or fieldnames. ",
    )

    @validator("parsers", "plugins", "processors", "stylers")
    def validate_importable(cls, v):
        try:
            for parser in v:
                import_string(parser.type)
        except Exception as e:
            raise ValueError(f"Invalid import: {parser.type} {e}") from e

        return v

    class Config:
        env_prefix = "TURMS_"
        extra = "forbid"


class Extensions(BaseModel):
    """Wrapping class to be able to extract the tums configuraiton"""

    turms: GeneratorConfig


class GraphQLProject(BaseSettings):
    """Configuration for the GraphQL project

    This is the main configuration for one GraphQL project. It is compliant with
    the graphql-config specification. And allows you to specify the schema and
    the documents that should be parsed.

    Turm will use the schema and documents to generate the python models, according
    to the generator configuration under extensions.turms
    """

    schema_url: Optional[Union[AnyHttpUrl, str]] = Field(alias="schema", env="schema")
    bearer_token: Optional[str] = None
    documents: Optional[str]
    extensions: Extensions

    class Config:
        env_prefix = "TURMS_GRAPHQL_"
        extra = "allow"


class GraphQLConfigMultiple(BaseSettings):
    """Configuration for multiple GraphQL projects

    This is the main configuration for multiple GraphQL projects. It is compliant with
    the graphql-config specification for multiple projec."""

    projects: Dict[str, GraphQLProject]

    class Config:
        extra = "allow"


class GraphQLConfigSingle(GraphQLProject):
    """Configuration for a single GraphQL project

    This is the main configuration for a single GraphQL project. It is compliant with
    the graphql-config specification for a single project.
    """

    class Config:
        extra = "allow"
