from pydantic import BaseModel
from typing import List


class GeneratorConfig(BaseModel):
    generated_name: str = "generated.py"

    object_bases: List[str] = ["herre.access.newobject.GraphQLObject"]
    interface_bases: List[str] = ["herre.access.newobject.GraphQLObject"]

    scalar_definitions = {
        "ID": "str",
        "String": "str",
        "Int": "int",
        "Boolean": "bool",
        "GenericScalar": "Dict",
    }

    additional_bases = {}
