"""Classes a generated client is mixed into, for the reserved_from tests."""

from pydantic import BaseModel


class WithGetBeastsField(BaseModel):
    get_beasts: int = 0


class WithGetBeastsMethod:
    def get_beasts(self) -> None: ...


class BeastApi:
    """Stands in for a previous generation of the client class being generated."""

    def get_beasts(self) -> None: ...


class ClientMixingInPreviousOutput(BeastApi):
    """A client that already mixes in the generated class, plus a name of its own."""

    def for_task(self) -> None: ...
