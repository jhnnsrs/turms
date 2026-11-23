from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def query(model: type[T], variables) -> T:
    return model(variables)  # pragma: nocover


async def aquery(model: type[T], variables) -> T:
    return model(variables)  # pragma: nocover


def subscribe(model: type[T], variables) -> T:
    yield model(variables)  # pragma: nocover
    yield model(variables)  # pragma: nocover


async def asubscribe(model: type[T], variables) -> T:
    yield model(variables)  # pragma: nocover
    yield model(variables)  # pragma: nocover


class ExtraArguments(BaseModel):
    extra: str | None


class ExtraOnOperations(BaseModel):
    extra: str | None


class ExtraArg(BaseModel):
    extra: str | None
