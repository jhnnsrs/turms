from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class StringQueryOperatorInput(BaseModel):
    eq: Optional[str]
    ne: Optional[str]
    in_: Optional[List[Optional[str]]] = Field(alias="in")
    nin: Optional[List[Optional[str]]]
    regex: Optional[str]
    glob: Optional[str]


class CountryFilterInput(BaseModel):
    code: Optional["StringQueryOperatorInput"]
    currency: Optional["StringQueryOperatorInput"]
    continent: Optional["StringQueryOperatorInput"]


class ContinentFilterInput(BaseModel):
    code: Optional["StringQueryOperatorInput"]


class LanguageFilterInput(BaseModel):
    code: Optional["StringQueryOperatorInput"]


ContinentFilterInput.update_forward_refs()
CountryFilterInput.update_forward_refs()
LanguageFilterInput.update_forward_refs()


class Country(BaseModel):
    code: str
    name: str
    native: str
    phone: str
    continent: "Continent"
    capital: Optional[str]
    currency: Optional[str]
    languages: List["Language"]
    emoji: str
    emoji_u: str = Field(alias="emojiU")
    states: List["State"]


class Continent(BaseModel):
    code: str
    name: str
    countries: List["Country"]


class Language(BaseModel):
    code: str
    name: Optional[str]
    native: Optional[str]
    rtl: bool


class State(BaseModel):
    code: Optional[str]
    name: str
    country: "Country"


class Query(BaseModel):
    _entities: List[Union["Country", "Continent", "Language"]]
    _service: "_Service"
    countries: List["Country"]
    country: Optional["Country"]
    continents: List["Continent"]
    continent: Optional["Continent"]
    languages: List["Language"]
    language: Optional["Language"]


class _Service(BaseModel):
    sdl: Optional[str]
    "The sdl representing the federated service capabilities. Includes federation directives, removes federation types, and includes rest of full schema after schema directives have been applied"


Query.update_forward_refs()
Country.update_forward_refs()
State.update_forward_refs()
