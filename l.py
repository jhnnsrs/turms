import strawberry
from typing import AsyncGenerator, Optional, List
from enum import Enum

@strawberry.type
class Beast:
    id: Optional[str] = strawberry.field(description='ID of beast (taken from binomial initial)')
    legs: Optional[int] = strawberry.field(description='number of legs beast has', deprecation_reason='use legsCount instead', directives=[])
    binomial: Optional[str] = strawberry.field(description="a beast's name in Latin")
    common_name: Optional[str] = strawberry.field(description="a beast's name to you and I")
    tax_class: Optional[str] = strawberry.field(description='taxonomy grouping')

    @strawberry.field(description="a beast's prey")
    def eats(self, t: Optional[bool], filter: str='nnn') -> Optional[List[Optional['Beast']]]:
        """a beast's prey"""
        return None
    is_eaten_by: Optional[List[Optional['Beast']]] = strawberry.field(description="a beast's predators")

@strawberry.type
class Query:

    @strawberry.field(description='get all the beasts on the server')
    def beasts(self) -> Optional[List[Optional[Beast]]]:
        """get all the beasts on the server"""
        return None

    @strawberry.field()
    def beast(self, id: str) -> Beast:
        return None

    @strawberry.field()
    def called_by(self, common_name: str) -> List[Optional[Beast]]:
        return None

@strawberry.type
class Mutation:

    @strawberry.mutation(description='create a massive beast on the server')
    def create_beast(self, id: str, legs: int, binomial: str, common_name: str, tax_class: str, eats: Optional[List[Optional[str]]]) -> Beast:
        """create a massive beast on the server"""
        return None

@strawberry.type
class Subscription:

    @strawberry.subscription()
    async def watch_beast(self, id: str) -> AsyncGenerator[Optional[Beast], None]:
        return None