from pydantic import AnyHttpUrl, BaseModel, Field
from typing import Dict, List, Optional, Union


class GeneratorConfig(BaseModel):
    domain: str = "default"
    out_dir: str = "api"
    generated_name: str = "schema.py"
    documents: Optional[str]

    object_bases: List[str] = ["turms.types.object.GraphQLObject"]
    interface_bases: Optional[List[str]] = None

    scalar_definitions = {}
    freeze: bool = False
    additional_bases = {}
    extensions: Dict = {}


class GraphQLConfig(BaseModel):
    schema_url: Optional[Union[AnyHttpUrl, str]] = Field(alias="schema")
    bearer_token: Optional[str] = None
    documents: Optional[str]
    domain: str = "default"
