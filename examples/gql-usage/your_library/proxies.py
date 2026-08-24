from gql import Client
from gql import gql


def execute(client: Client, operation, variables):
    serverresult = client.execute(gql(operation.Meta.document), operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True))
    return operation(**serverresult)


def subscribe(client: Client, operation, variables):
    for event in client.subscribe(
        gql(operation.Meta.document), operation.Arguments(**variables).model_dump(by_alias=True, exclude_unset=True)
    ):
        yield operation(**event)

