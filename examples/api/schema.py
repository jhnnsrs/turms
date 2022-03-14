from enum import Enum
from typing import List, Literal, Optioanl, Optional

from arkitekt.funcs import aexecute, execute
from arkitekt.rath import ArkitektRath
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


async def acreate_beast(
    nested: List[Optional[List[Optional[str]]]] = None,
    non_optional_parameter: Optional[str] = "999",
    rath: ArkitektRath = None,
) -> CreateBeastCreatebeast:
    """createBeast

    Genrates a best which is nice

    Arguments:
        nested (List[List[str]], optional): nested.
        non_optional_parameter (Optional[str], optional): nonOptionalParameter. Defaults to 999
        rath (arkitekt.rath.ArkitektRath, optional): The arkitekt rath client

    Returns:
        CreateBeastCreatebeast"""
    return (
        await aexecute(
            CreateBeast,
            {"nested": nested, "nonOptionalParameter": non_optional_parameter},
            rath=rath,
        )
    ).create_beast


def create_beast(
    nested: List[Optional[List[Optional[str]]]] = None,
    non_optional_parameter: Optional[str] = "999",
    rath: ArkitektRath = None,
) -> CreateBeastCreatebeast:
    """createBeast

    Genrates a best which is nice

    Arguments:
        nested (List[List[str]], optional): nested.
        non_optional_parameter (Optional[str], optional): nonOptionalParameter. Defaults to 999
        rath (arkitekt.rath.ArkitektRath, optional): The arkitekt rath client

    Returns:
        CreateBeastCreatebeast"""
    return execute(
        CreateBeast,
        {"nested": nested, "nonOptionalParameter": non_optional_parameter},
        rath=rath,
    ).create_beast


async def acreate_int_beast(
    nested: List[Optional[List[Optional[str]]]] = None,
    non_optional_parameter: Optional[int] = 999,
    rath: ArkitektRath = None,
) -> CreateIntBeastCreateintbeast:
    """createIntBeast



    Arguments:
        nested (List[List[str]], optional): nested.
        non_optional_parameter (Optional[int], optional): nonOptionalParameter. Defaults to 999
        rath (arkitekt.rath.ArkitektRath, optional): The arkitekt rath client

    Returns:
        CreateIntBeastCreateintbeast"""
    return (
        await aexecute(
            CreateIntBeast,
            {"nested": nested, "nonOptionalParameter": non_optional_parameter},
            rath=rath,
        )
    ).create_int_beast


def create_int_beast(
    nested: List[Optional[List[Optional[str]]]] = None,
    non_optional_parameter: Optional[int] = 999,
    rath: ArkitektRath = None,
) -> CreateIntBeastCreateintbeast:
    """createIntBeast



    Arguments:
        nested (List[List[str]], optional): nested.
        non_optional_parameter (Optional[int], optional): nonOptionalParameter. Defaults to 999
        rath (arkitekt.rath.ArkitektRath, optional): The arkitekt rath client

    Returns:
        CreateIntBeastCreateintbeast"""
    return execute(
        CreateIntBeast,
        {"nested": nested, "nonOptionalParameter": non_optional_parameter},
        rath=rath,
    ).create_int_beast
