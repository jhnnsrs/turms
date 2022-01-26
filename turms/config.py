from pydantic import AnyHttpUrl, BaseModel, Field
from typing import Dict, List, Optional, Union


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

    prepend_fragment: str = ""
    append_fragment: str = "Fragment"
    prepend_query: str = ""
    append_query: str = "Query"
    prepend_mutation: str = ""
    append_mutation: str = "Mutation"
    prepend_subscription: str = ""
    append_subscription: str = "Subscription"

    prepend_input: str = ""
    append_input: str = ""
    prepend_enum: str = ""
    append_enum: str = ""


class GraphQLConfig(BaseModel):
    schema_url: Optional[Union[AnyHttpUrl, str]] = Field(alias="schema")
    documents: Optional[str]
    domain: str = "default"
