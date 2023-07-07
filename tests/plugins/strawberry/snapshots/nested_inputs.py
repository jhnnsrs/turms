import strawberry
from typing import List, Optional

@strawberry.input
class RemoveItemFromPlaylistTrackInput:
    uri: str

@strawberry.input
class RemoveItemFromPlaylistInput:
    playlistId: str
    snapshotId: Optional[str]
    tracks: List[RemoveItemFromPlaylistTrackInput]

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> Optional[str]:
        return None
