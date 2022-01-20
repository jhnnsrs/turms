from pydantic import AnyHttpUrl, BaseModel
from typing import List, Optional

from pyparsing import Opt


class GeneratorConfig(BaseModel):
    domain: str = "default"
    schema_url: Optional[AnyHttpUrl]
    schema_file: Optional[str]
    out_dir: str = "api"
    generated_name: str = "schema.py"

    object_bases: List[str] = ["turms.types.object.GraphQLObject"]
    interface_bases: List[str] = ["turms.types.object.GraphQLObject"]

    scalar_definitions = {
        "ID": "str",
        "String": "str",
        "Int": "int",
        "Boolean": "bool",
        "GenericScalar": "Dict",
    }

    additional_bases = {}
