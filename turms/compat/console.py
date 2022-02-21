from contextlib import contextmanager


try:
    from rich.console import Console
    from rich import get_console
except ImportError:

    class Console:
        def __init__(self) -> None:
            pass

        def print(self, *args, **kwargs) -> None:
            print(*args, **kwargs)

        def warn(self, *args, **kwargs) -> None:
            print(*args, **kwargs)

        def error(self, *args, **kwargs) -> None:
            print(*args, **kwargs)

        def status(self):
            @contextmanager
            def x(*args, **kwargs):
                yield x

            return x

    def get_console():
        return Console()
