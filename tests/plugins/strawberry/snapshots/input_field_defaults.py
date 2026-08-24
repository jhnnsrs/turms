import strawberry


@strawberry.input
class FieldDefaultsInput:
    nullableNoDefault: str | None = strawberry.field(default=None)
    nullableWithDefault: str | None = strawberry.field(default='fallback')
    requiredWithDefault: str = strawberry.field(default='required-fallback')
    requiredNoDefault: str

@strawberry.type
class Query:

    @strawberry.field()
    def hi(self) -> str | None:
        return None