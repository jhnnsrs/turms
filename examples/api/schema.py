from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CreateBeastCreatebeast(BaseModel):
    typename: Optional[Literal["Beast"]] = Field(alias="__typename")
    binomial: Optional[str]
    "a beast's name in Latin"


class CreateBeast(BaseModel):
    create_beast: Optional[CreateBeastCreatebeast] = Field(alias="createBeast")
    "Genrates a best which is nice"

    class Meta:
        domain = "default"
        document = 'mutation createBeast($nested: [[String!]!], $nonOptionalParameter: String! = "999") {\n  createBeast(nested: $nested, nonOptionalParameter: $nonOptionalParameter) {\n    binomial\n  }\n}'


class CreateIntBeastCreateintbeast(BaseModel):
    typename: Optional[Literal["Beast"]] = Field(alias="__typename")
    binomial: Optional[str]
    "a beast's name in Latin"


class CreateIntBeast(BaseModel):
    create_int_beast: Optional[CreateIntBeastCreateintbeast] = Field(
        alias="createIntBeast"
    )

    class Meta:
        domain = "default"
        document = "mutation createIntBeast($nested: [[String!]!], $nonOptionalParameter: Int! = 999) {\n  createIntBeast(nested: $nested, nonOptionalParameter: $nonOptionalParameter) {\n    binomial\n  }\n}"
