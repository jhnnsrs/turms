import strawberry
from typing import Optional
from enum import Enum

@strawberry.input
class RemoveItemFromPlaylistTrackInput:
    uri: str

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> Optional[str]:
        return None