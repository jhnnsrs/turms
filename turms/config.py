import builtins
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Field, validator
from typing import Any, Dict, List, Optional, Union
from turms.helpers import import_string
from enum import Enum


class ConfigProxy(BaseModel):
    type: str

    class Config:
        extra = "allow"


class PythonScalar(str):
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
    domain: Optional[str] = None
    out_dir: str = "api"
    generated_name: str = "schema.py"
    documents: Optional[str]
    verbose: bool = False

    object_bases: List[str] = ["pydantic.BaseModel"]
    interface_bases: Optional[List[str]] = None
    always_resolve_interfaces: bool = True

    scalar_definitions: Dict[str, PythonScalar] = {}
    freeze: FreezeConfig = Field(default_factory=FreezeConfig)

    additional_bases = {}
    additional_config: Dict[str, Dict[str, Any]] = {}
    force_plugin_order: bool = True

    parsers: List[ConfigProxy] = []
    plugins: List[ConfigProxy] = []
    processors: List[ConfigProxy] = []
    stylers: List[ConfigProxy] = []

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
    turms: GeneratorConfig


class GraphQLProject(BaseSettings):
    schema_url: Optional[Union[AnyHttpUrl, str]] = Field(alias="schema", env="schema")
    bearer_token: Optional[str] = None
    documents: Optional[str]
    extensions: Extensions

    class Config:
        env_prefix = "TURMS_GRAPHQL_"
        extra = "allow"


class GraphQLConfigMultiple(BaseSettings):
    projects: Dict[str, GraphQLProject]

    class Config:
        extra = "allow"


class GraphQLConfigSingle(GraphQLProject):
    class Config:
        extra = "allow"
