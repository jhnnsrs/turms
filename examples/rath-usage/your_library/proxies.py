from rath import Rath
from rath.rath import current_rath


def execute(operation, variables, rath: Rath = None):
    rath = rath or current_rath.get()
    return operation(
        **rath.query(
            operation.Meta.document,
            operation.Arguments(**variables).dict(by_alias=True),
        ).data
    )


async def aexecute(operation, variables, rath: Rath = None):
    rath = rath or current_rath.get()
    x = await rath.aquery(
        operation.Meta.document, operation.Arguments(**variables).dict(by_alias=True)
    )
    return operation(**x.data)


def subscribe(operation, variables, rath: Rath = None):
    rath = rath or current_rath.get()

    for ev in rath.subscribe(
        operation.Meta.document, operation.Arguments(**variables).dict(by_alias=True)
    ):
        yield operation(**ev.data)


async def asubscribe(operation, variables, rath: Rath = None):
    rath = rath or current_rath.get()
    async for event in rath.asubscribe(
        operation.Meta.document, operation.Arguments(**variables).dict(by_alias=True)
    ):
        yield operation(**event.data)
