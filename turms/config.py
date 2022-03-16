from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Field, validator
from typing import Dict, List, Optional, Union
from turms.helpers import import_string
from turms.parsers.base import ParserConfig
from turms.plugins.base import PluginConfig
from turms.processors.base import ProcessorConfig
from turms.stylers.base import StylerConfig


class ConfigProxy(BaseModel):
    type: str

    class Config:
        extras = "allow"


class GeneratorConfig(BaseSettings):
    domain: str = "default"
    out_dir: str = "api"
    generated_name: str = "schema.py"
    documents: Optional[str]
    verbose: bool = False

    object_bases: List[str] = ["pydantic.BaseModel"]
    interface_bases: Optional[List[str]] = None
    always_resolve_interfaces: bool = True

    scalar_definitions = {}
    freeze: bool = False
    additional_bases = {}
    extensions: Dict = {}

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


class GraphQLConfig(BaseSettings):  # TODO: Rename to graphql project
    schema_url: Optional[Union[AnyHttpUrl, str]] = Field(alias="schema", env="schema")
    bearer_token: Optional[str] = None
    documents: Optional[str]
    domain: str = "default"
    extensions: Extensions

    class Config:
        env_prefix = "TURMS_GRAPHQL_"
        extra = "allow"
