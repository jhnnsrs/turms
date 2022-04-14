from pydantic import Field, BaseModel
from typing import Optional, List, Literal
from enum import Enum

class StringQueryOperatorInput(BaseModel):
    eq: Optional[str]
    ne: Optional[str]
    in_: Optional[List[Optional[str]]] = Field(alias='in')
    nin: Optional[List[Optional[str]]]
    regex: Optional[str]
    glob: Optional[str]

class CountryFilterInput(BaseModel):
    code: Optional['StringQueryOperatorInput']
    currency: Optional['StringQueryOperatorInput']
    continent: Optional['StringQueryOperatorInput']

class ContinentFilterInput(BaseModel):
    code: Optional['StringQueryOperatorInput']

class LanguageFilterInput(BaseModel):
    code: Optional['StringQueryOperatorInput']
StringQueryOperatorInput.update_forward_refs()

class CountriesCountries(BaseModel):
    typename: Optional[Literal['Country']] = Field(alias='__typename')
    phone: str
    capital: Optional[str]

class Countries(BaseModel):
    countries: List[CountriesCountries]

    class Arguments(BaseModel):
        pass

    class Meta:
        document = 'query Countries {\n  countries {\n    phone\n    capital\n  }\n}'

def countries() -> List[CountriesCountries]:
    """Countries 



Arguments:

Returns:
    Countries"""
    return func(Countries, {}).countries



Countries()