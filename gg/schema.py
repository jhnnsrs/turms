from typing import List, Optional, Literal
from api.proxies import execute
from enum import Enum
from pydantic import Field, BaseModel
from gql.client import AsyncClientSession


class Beast(BaseModel):
    typename: Optional[Literal["Beast"]] = Field(alias="__typename")
    common_name: Optional[str] = Field(alias="commonName")
    "a beast's name to you and I"
    tax_class: Optional[str] = Field(alias="taxClass")
    "taxonomy grouping"


class CreateBeastCreatebeast(BaseModel):
    typename: Optional[Literal["Beast"]] = Field(alias="__typename")
    binomial: Optional[str]
    "a beast's name in Latin"
    common_name: Optional[str] = Field(alias="commonName")
    "a beast's name to you and I"


class CreateBeast(BaseModel):
    create_beast: CreateBeastCreatebeast = Field(alias="createBeast")
    "create a massive beast on the server"

    class Arguments(BaseModel):
        id: str
        legs: int
        binomial: str
        common_name: str = Field(alias="commonName")
        tax_class: str = Field(alias="taxClass")
        eats: Optional[List[Optional[str]]] = Field(default=None)

    class Meta:
        document = "mutation createBeast($id: ID!, $legs: Int!, $binomial: String!, $commonName: String!, $taxClass: String!, $eats: [ID]) {\n  createBeast(\n    id: $id\n    legs: $legs\n    binomial: $binomial\n    commonName: $commonName\n    taxClass: $taxClass\n    eats: $eats\n  ) {\n    binomial\n    commonName\n  }\n}"


class Get_beasts(BaseModel):
    beasts: Optional[List[Optional[Beast]]]
    "get all the beasts on the server"

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Beast on Beast {\n  commonName\n  taxClass\n}\n\nquery get_beasts {\n  beasts {\n    ...Beast\n  }\n}"


async def acreate_beast(
    client: AsyncClientSession,
    id: str,
    legs: int,
    binomial: str,
    common_name: str,
    tax_class: str,
    eats: Optional[List[Optional[str]]] = None,
) -> CreateBeastCreatebeast:
    """createBeast



    Arguments:
        client (gql.client.AsyncClientSession): Specify that in turms.plugin.funcs.OperationsFuncPlugin
        id (str): id
        legs (int): legs
        binomial (str): binomial
        common_name (str): commonName
        tax_class (str): taxClass
        eats (Optional[List[Optional[str]]], optional): eats.

    Returns:
        CreateBeastCreatebeast"""
    return (
        await execute(
            client,
            CreateBeast,
            {
                "id": id,
                "legs": legs,
                "binomial": binomial,
                "common_name": common_name,
                "tax_class": tax_class,
                "eats": eats,
            },
        )
    ).create_beast


async def aget_beasts(client: AsyncClientSession) -> Optional[List[Optional[Beast]]]:
    """get_beasts



    Arguments:
        client (gql.client.AsyncClientSession): Specify that in turms.plugin.funcs.OperationsFuncPlugin

    Returns:
        Optional[List[Optional[Beast]]]"""
    return (await execute(client, Get_beasts, {})).beasts
