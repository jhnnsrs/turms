from typing import Any, List, Optional
from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic.main import BaseModel
from turms.types.utils import clean_dict

# Mixin CLass is not Possible because of BaseModel Metaclass


class GraphQLObject(BaseModel):
    typename: Optional[str] = Field(alias="__typename")

    def __init__(__pydantic_self__, **data: Any) -> None:
        if "__typename" not in data:
            data["__typename"] = __pydantic_self__.__class__.__name__
        super().__init__(**data)

    @validator("typename")
    def typename_matches_class(cls, v):
        if v is None:
            return (
                None  # We are ommiting typechecks if __typename is not explicitly set
            )
        if cls.__name__ == v:
            return v
        raise ValueError(f"Didn't find correct class {cls.__name__} __typename {v}")

    def dict(self, *args, by_alias=True, **kwargs):
        return super().dict(
            *args,
            **{
                **kwargs,
                "by_alias": by_alias,
            },
        )

    async def to_variable(self):
        dictionary = self.dict(exclude={"typename"})
        clean_dict(dictionary, lambda key: key == "__typename")
        return dictionary
