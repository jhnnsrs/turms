from enum import Enum
from typing import List, Optional

from mikro.funcs import aexecute, execute
from mikro.mikro import MikroRath
from pydantic import BaseModel, Field
from typing_extensions import Literal


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


async def acreate_beast(
    nested: Optional[List[List[str]]] = None,
    non_optional_parameter: str = "999",
    mikrorath: MikroRath = None,
) -> Optional[CreateBeastCreatebeast]:
    """createBeast

    Genrates a best which is nice

    Arguments:
        nested (Optional[List[List[str]]], optional): nested.
        non_optional_parameter (str, optional): nonOptionalParameter. Defaults to 999
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        CreateBeastCreatebeast"""
    return (
        await aexecute(
            CreateBeast,
            {"nested": nested, "nonOptionalParameter": non_optional_parameter},
            mikrorath=mikrorath,
        )
    ).create_beast


def create_beast(
    nested: Optional[List[List[str]]] = None,
    non_optional_parameter: str = "999",
    mikrorath: MikroRath = None,
) -> Optional[CreateBeastCreatebeast]:
    """createBeast

    Genrates a best which is nice

    Arguments:
        nested (Optional[List[List[str]]], optional): nested.
        non_optional_parameter (str, optional): nonOptionalParameter. Defaults to 999
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        CreateBeastCreatebeast"""
    return execute(
        CreateBeast,
        {"nested": nested, "nonOptionalParameter": non_optional_parameter},
        mikrorath=mikrorath,
    ).create_beast


async def acreate_int_beast(
    nested: Optional[List[List[str]]] = None,
    non_optional_parameter: int = 999,
    mikrorath: MikroRath = None,
) -> Optional[CreateIntBeastCreateintbeast]:
    """createIntBeast



    Arguments:
        nested (Optional[List[List[str]]], optional): nested.
        non_optional_parameter (int, optional): nonOptionalParameter. Defaults to 999
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        CreateIntBeastCreateintbeast"""
    return (
        await aexecute(
            CreateIntBeast,
            {"nested": nested, "nonOptionalParameter": non_optional_parameter},
            mikrorath=mikrorath,
        )
    ).create_int_beast


def create_int_beast(
    nested: Optional[List[List[str]]] = None,
    non_optional_parameter: int = 999,
    mikrorath: MikroRath = None,
) -> Optional[CreateIntBeastCreateintbeast]:
    """createIntBeast



    Arguments:
        nested (Optional[List[List[str]]], optional): nested.
        non_optional_parameter (int, optional): nonOptionalParameter. Defaults to 999
        mikrorath (mikro.mikro.MikroRath, optional): The mikro rath client

    Returns:
        CreateIntBeastCreateintbeast"""
    return execute(
        CreateIntBeast,
        {"nested": nested, "nonOptionalParameter": non_optional_parameter},
        mikrorath=mikrorath,
    ).create_int_beast
