from pydantic import ConfigDict, Field, BaseModel
from enum import Enum
from typing import Literal, Optional, List
from api.proxies import execute
from gql.client import AsyncClientSession


class Beast(BaseModel):
    """No documentation"""

    typename: Literal["Beast"] = Field(alias="__typename", default="Beast")
    common_name: Optional[str] = Field(default=None, alias="commonName")
    "a beast's name to you and I"
    tax_class: Optional[str] = Field(default=None, alias="taxClass")
    "taxonomy grouping"


class CreateBeastCreatebeast(BaseModel):
    """No documentation"""

    typename: Literal["Beast"] = Field(alias="__typename", default="Beast")
    binomial: Optional[str] = Field(default=None)
    "a beast's name in Latin"
    common_name: Optional[str] = Field(default=None, alias="commonName")
    "a beast's name to you and I"


class CreateBeast(BaseModel):
    """No documentation found for this operation."""

    create_beast: CreateBeastCreatebeast = Field(alias="createBeast")
    "create a massive beast on the server"

    class Arguments(BaseModel):
        """Arguments for createBeast"""

        id: str
        legs: int
        binomial: str
        common_name: str = Field(alias="commonName")
        tax_class: str = Field(alias="taxClass")
        eats: Optional[List[Optional[str]]] = Field(default=None)
        model_config = ConfigDict(populate_by_name=None)

    class Meta:
        """Meta class for createBeast"""

        document = "mutation createBeast($id: ID!, $legs: Int!, $binomial: String!, $commonName: String!, $taxClass: String!, $eats: [ID]) {\n  createBeast(\n    id: $id\n    legs: $legs\n    binomial: $binomial\n    commonName: $commonName\n    taxClass: $taxClass\n    eats: $eats\n  ) {\n    binomial\n    commonName\n    __typename\n  }\n}"


class Get_beasts(BaseModel):
    """No documentation found for this operation."""

    beasts: Optional[List[Optional[Beast]]] = Field(default=None)
    "get all the beasts on the server"

    class Arguments(BaseModel):
        """Arguments for get_beasts"""

        model_config = ConfigDict(populate_by_name=None)

    class Meta:
        """Meta class for get_beasts"""

        document = "fragment Beast on Beast {\n  commonName\n  taxClass\n  __typename\n}\n\nquery get_beasts {\n  beasts {\n    ...Beast\n    __typename\n  }\n}"


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

    create a massive beast on the server

    Arguments:
        client (gql.client.AsyncClientSession): Specify that in turms.plugin.funcs.OperationsFuncPlugin
        id (str): No description
        legs (int): No description
        binomial (str): No description
        common_name (str): No description
        tax_class (str): No description
        eats (Optional[List[Optional[str]]], optional): No description.

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
                "commonName": common_name,
                "taxClass": tax_class,
                "eats": eats,
            },
        )
    ).create_beast


async def aget_beasts(client: AsyncClientSession) -> Optional[List[Optional[Beast]]]:
    """get_beasts

    get all the beasts on the server

    Arguments:
        client (gql.client.AsyncClientSession): Specify that in turms.plugin.funcs.OperationsFuncPlugin

    Returns:
        Optional[List[Optional[Beast]]]"""
    return (await execute(client, Get_beasts, {})).beasts
