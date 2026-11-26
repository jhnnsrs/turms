from collections.abc import Iterator, Mapping
from typing import Any, Protocol, TypeVar

from gql import Client, gql
from pydantic import BaseModel


class OperationMeta(Protocol):
    document: str


class Operation(Protocol):
    """What turms generates for an operation: its document, arguments and result."""

    Meta: type[OperationMeta]
    Arguments: type[BaseModel]

    def __init__(self, **data: Any) -> None: ...


TOperation = TypeVar("TOperation", bound=Operation)


def execute(
    client: Client, operation: type[TOperation], variables: Mapping[str, Any]
) -> TOperation:
    serverresult = client.execute(
        gql(operation.Meta.document),
        operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True),
    )
    return operation(**serverresult)


def subscribe(
    client: Client, operation: type[TOperation], variables: Mapping[str, Any]
) -> Iterator[TOperation]:
    for event in client.subscribe(
        gql(operation.Meta.document),
        operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True),
    ):
        yield operation(**event)
