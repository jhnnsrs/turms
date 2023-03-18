from watchfiles.filters import BaseFilter
from watchfiles import watch
import os


class GraphQLFilter(BaseFilter):  # pragma: no cover
    def __call__(self, change, path: str) -> bool:
        x = super().__call__(change, path)
        if not x:
            return False

        x = os.path.basename(path)
        fileending = x.split(".")[1]

        return fileending == "graphql"


def stream_changes(folder: str):  # pragma: no cover
    for changes in watch(".", watch_filter=GraphQLFilter(), debounce=2000, step=500):
        yield changes
