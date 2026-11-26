"""What the generated functions call to actually run an operation.

Turms generates one function per operation and points it here via the
``definitions`` list in ``graphql.config.yaml``. Nothing about this file is
generated -- it is the seam where you say what "executing" means for your
client. Swap rath for something else and only this file changes.
"""

from collections.abc import AsyncIterator, Iterator, Mapping
from typing import Any

from rath import Rath
from rath.turms.funcs import TOperation


def execute(
    operation: type[TOperation], variables: Mapping[str, Any], rath: Rath
) -> TOperation:
    return operation(
        **rath.query(
            operation.Meta.document,
            operation.Arguments(**variables).model_dump(
                by_alias=True, exclude_unset=True
            ),
        ).data
    )


async def aexecute(
    operation: type[TOperation], variables: Mapping[str, Any], rath: Rath
) -> TOperation:
    x = await rath.aquery(
        operation.Meta.document,
        operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True),
    )
    return operation(**x.data)


def subscribe(
    operation: type[TOperation], variables: Mapping[str, Any], rath: Rath
) -> Iterator[TOperation]:
    for ev in rath.subscribe(
        operation.Meta.document,
        operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True),
    ):
        yield operation(**ev.data)


async def asubscribe(
    operation: type[TOperation], variables: Mapping[str, Any], rath: Rath
) -> AsyncIterator[TOperation]:
    async for event in rath.asubscribe(
        operation.Meta.document,
        operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True),
    ):
        yield operation(**event.data)
