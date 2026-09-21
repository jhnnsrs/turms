"""What the generated functions call to actually run an operation.

Turms generates one function per operation and points it here via the
``definitions`` list in ``graphql.config.yaml``. Nothing about this file is
generated -- it is the seam where you say what "executing" means for your
client. Swap rath for something else and only this file changes.
"""

from rath import Rath


def execute(operation, variables, rath: Rath):
    return operation(
        **rath.query(
            operation.Meta.document,
            operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True),
        ).data
    )


async def aexecute(operation, variables, rath: Rath):
    x = await rath.aquery(
        operation.Meta.document, operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True)
    )
    return operation(**x.data)


def subscribe(operation, variables, rath: Rath):
    for ev in rath.subscribe(
        operation.Meta.document, operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True)
    ):
        yield operation(**ev.data)


async def asubscribe(operation, variables, rath: Rath):
    async for event in rath.asubscribe(
        operation.Meta.document, operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True)
    ):
        yield operation(**event.data)
