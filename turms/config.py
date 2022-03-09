from pydantic import AnyHttpUrl, BaseModel, BaseSettings, Field
from typing import Dict, List, Optional, Union


class GeneratorConfig(BaseSettings):
    domain: str = "default"
    out_dir: str = "api"
    generated_name: str = "schema.py"
    documents: Optional[str]

    object_bases: List[str] = ["pydantic.BaseModel"]
    interface_bases: Optional[List[str]] = None
    always_resolve_interfaces: bool = True

    scalar_definitions = {}
    freeze: bool = False
    additional_bases = {}
    extensions: Dict = {}

    class Config:
        extra = "allow"


class GraphQLConfig(BaseSettings):
    schema_url: Optional[Union[AnyHttpUrl, str]] = Field(alias="schema")
    bearer_token: Optional[str] = None
    documents: Optional[str]
    domain: str = "default"

    class Config:
        extra = "allow"
