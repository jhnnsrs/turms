import os
from collections.abc import Generator

from watchfiles import Change, watch
from watchfiles.filters import BaseFilter


class GraphQLFilter(BaseFilter):  # pragma: no cover
    def __call__(self, change: Change, path: str) -> bool:
        x = super().__call__(change, path)
        if not x:
            return False

        x = os.path.basename(path)
        fileending = x.split(".")[1]

        return fileending == "graphql"


def stream_changes(
    folder: str | None,
) -> Generator[set[tuple[Change, str]], None, None]:  # pragma: no cover
    # A plain loop, not `yield from`: closing this generator leaves watch() as it was.
    for changes in watch(  # noqa: UP028
        ".", watch_filter=GraphQLFilter(), debounce=2000, step=500
    ):
        yield changes
