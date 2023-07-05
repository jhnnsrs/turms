import strawberry
from typing import Optional

@strawberry.input
class RemoveItemFromPlaylistTrackInput:
    uri: str

@strawberry.input
class RemoveItemFromPlaylistInput:
    playlistId: str
    snapshotId: Optional[str]
    tracks: RemoveItemFromPlaylistTrackInput

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> Optional[str]:
        return None