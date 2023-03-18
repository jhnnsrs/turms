from typing import List, Literal, Optional

from pydantic import BaseModel, Field


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


class Get_countriesCountries(BaseModel):
    typename: Optional[Literal["Country"]] = Field(alias="__typename")
    code: str
    name: str
    continent: Continent


class Get_countries(BaseModel):
    countries: List[Get_countriesCountries]

    class Arguments(BaseModel):
        filter: Optional[CountryFilterInput] = None

    class Meta:
        document = "fragment Continent on Continent {\n  code\n  name\n}\n\nquery get_countries($filter: CountryFilterInput) {\n  countries(filter: $filter) {\n    code\n    name\n    continent {\n      ...Continent\n    }\n  }\n}"
