import strawberry
from enum import Enum
from typing import Optional

@strawberry.input
class RemoveItemFromPlaylistTrackInput:
    uri: str

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> Optional[str]:
        return None