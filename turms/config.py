import builtins
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Field, validator
from typing import Dict, List, Optional, Union
from turms.helpers import import_string


class ConfigProxy(BaseModel):
    type: str

    class Config:
        extra = "allow"


class PythonScalar(str):

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        # __modify_schema__ should mutate the dict it receives in place,
        # the returned value will be ignored
        return field_schema

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("string required")

        if v not in dir(builtins):
            try:
                import_string(v)
            except Exception as e:
                raise ValueError(f"Invalid scalar: {v} {e}") from e    
        # you could also return a string here which would mean model.post_code
        # would be a string, pydantic won't care but you could end up with some
        # confusion since the value's type won't match the type annotation
        # exactly
        return cls(v)



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
    freeze: bool = False
    additional_bases = {}
    force_plugin_order = True

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
