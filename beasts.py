import strawberry
from strawberry import ID
from typing import Optional, List, AsyncGenerator
from enum import Enum


@strawberry.type
class Beast:
    id: Optional[ID] = strawberry.field(
        description="ID of beast (taken from binomial initial)"
    )
    legs: Optional[int] = strawberry.field(description="number of legs beast has")
    binomial: Optional[str] = strawberry.field(description="a beast's name in Latin")
    common_name: Optional[str] = strawberry.field(
        description="a beast's name to you and I"
    )
    tax_class: Optional[str] = strawberry.field(description="taxonomy grouping")
    eats: Optional[List[Optional["Beast"]]] = strawberry.field(
        description="a beast's prey"
    )
    is_eaten_by: Optional[List[Optional["Beast"]]] = strawberry.field(
        description="a beast's predators"
    )


@strawberry.type
class Query:
    @strawberry.field(description="get all the beasts on the server")
    def beasts(self) -> Optional[List[Optional[Beast]]]:
        """get all the beasts on the server"""
        return None

    @strawberry.field()
    def beast(self, id: ID) -> Beast:
        return None

    @strawberry.field()
    def called_by(self, common_name: str) -> List[Optional[Beast]]:
        return None


@strawberry.type
class Mutation:
    @strawberry.mutation(description="create a massive beast on the server")
    def create_beast(
        self,
        id: ID,
        legs: int,
        binomial: str,
        common_name: str,
        tax_class: str,
        eats: Optional[List[Optional[ID]]],
    ) -> Beast:
        """create a massive beast on the server"""
        return None


@strawberry.type
class Subscription:
    @strawberry.subscription()
    async def watch_beast(self, id: ID) -> AsyncGenerator[Optional[Beast], None]:
        return None
