from typing import Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def query(model: Type[T], variables) -> T:
    return model(variables)


async def aquery(model: Type[T], variables) -> T:
    return model(variables)


def subscribe(model: Type[T], variables) -> T:
    yield model(variables)
    yield model(variables)


async def asubscribe(model: Type[T], variables) -> T:
    yield model(variables)
    yield model(variables)


class ExtraArguments(BaseModel):
    extra: Optional[str]


class ExtraOnOperations(BaseModel):
    extra: Optional[str]
