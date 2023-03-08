from typing import List, Literal, Optional

from pydantic import BaseModel, Field
from rath import Rath

from your_library.proxies import aexecute, execute


class StringQueryOperatorInput(BaseModel):
    eq: Optional[str]
    ne: Optional[str]
    in_: Optional[List[Optional[str]]] = Field(alias="in")
    nin: Optional[List[Optional[str]]]
    regex: Optional[str]
    glob: Optional[str]


class CountryFilterInput(BaseModel):
    code: Optional[StringQueryOperatorInput]
    currency: Optional[StringQueryOperatorInput]
    continent: Optional[StringQueryOperatorInput]


class ContinentFilterInput(BaseModel):
    code: Optional[StringQueryOperatorInput]


class LanguageFilterInput(BaseModel):
    code: Optional[StringQueryOperatorInput]


class Continent(BaseModel):
    typename: Optional[Literal["Continent"]] = Field(alias="__typename")
    code: str
    name: str


class Get_capsulesCountries(BaseModel):
    typename: Optional[Literal["Country"]] = Field(alias="__typename")
    code: str
    name: str
    continent: Continent


class Get_capsules(BaseModel):
    countries: List[Get_capsulesCountries]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = "fragment Continent on Continent {\n  code\n  name\n}\n\nquery get_capsules {\n  countries {\n    code\n    name\n    continent {\n      ...Continent\n    }\n  }\n}"


async def aget_capsules(rath: Rath = None) -> List[Get_capsulesCountries]:
    """get_capsules



    Arguments:
        rath (rath.Rath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Get_capsulesCountries]"""
    return (await aexecute(Get_capsules, {}, rath=rath)).countries


def get_capsules(rath: Rath = None) -> List[Get_capsulesCountries]:
    """get_capsules



    Arguments:
        rath (rath.Rath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[Get_capsulesCountries]"""
    return execute(Get_capsules, {}, rath=rath).countries
