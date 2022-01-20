from ast import alias
from pydantic import AnyHttpUrl, BaseModel, Field
from typing import Dict, List, Optional


class GeneratorConfig(BaseModel):
    domain: str = "default"
    out_dir: str = "api"
    generated_name: str = "schema.py"
    documents: Optional[str]

    object_bases: List[str] = ["turms.types.object.GraphQLObject"]
    interface_bases: List[str] = ["turms.types.object.GraphQLObject"]

    scalar_definitions = {}

    additional_bases = {}
    extensions: Dict = {}


class GraphQLConfig(BaseModel):
    schema_url: Optional[AnyHttpUrl] = Field(alias="schema")
    documents: Optional[str]
