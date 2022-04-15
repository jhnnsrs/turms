from typing import Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def query(model: Type[T], variables) -> T:
    return model(variables)  # pragma: nocover


async def aquery(model: Type[T], variables) -> T:
    return model(variables)  # pragma: nocover


def subscribe(model: Type[T], variables) -> T:
    yield model(variables)  # pragma: nocover
    yield model(variables)  # pragma: nocover


async def asubscribe(model: Type[T], variables) -> T:
    yield model(variables)  # pragma: nocover
    yield model(variables)  # pragma: nocover


class ExtraArguments(BaseModel):
    extra: Optional[str]


class ExtraOnOperations(BaseModel):
    extra: Optional[str]


class ExtraArg(BaseModel):
    extra: Optional[str]
