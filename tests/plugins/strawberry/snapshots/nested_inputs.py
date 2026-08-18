import strawberry


@strawberry.input
class RemoveItemFromPlaylistTrackInput:
    uri: str

@strawberry.input
class RemoveItemFromPlaylistInput:
    playlistId: str
    snapshotId: str | None
    tracks: list[RemoveItemFromPlaylistTrackInput]

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> str | None:
        return None