import strawberry


@strawberry.input
class FieldDefaultsInput:
    nullableNoDefault: str | None = strawberry.field(default=None)
    nullableWithDefault: str | None = strawberry.field(default='fallback')
    requiredWithDefault: str = strawberry.field(default='required-fallback')
    requiredNoDefault: str
    nullableListWithDefault: list[str] | None = strawberry.field(default_factory=lambda: ['a', 'b'])

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> str | None:
        return None