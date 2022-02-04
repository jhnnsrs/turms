from typing import Any, List, Optional
from pydantic.class_validators import validator
from pydantic.fields import Field
from pydantic.main import BaseModel
from turms.types.utils import clean_dict

# Mixin CLass is not Possible because of BaseModel Metaclass


class GraphQLObjectError(Exception):
    pass


class GraphQLObject(BaseModel):
    def dict(self, *args, by_alias=True, **kwargs):

        return super().dict(
            *args,
            **{
                **kwargs,
                "by_alias": by_alias,
            },
        )

    async def shrink(self):
        """WIll be called by the ward"""
        assert (
            self.id
        ), "Cannot convert an object to a variable if you didn't query its unique id"
        return self.id

    def shrink(self):
        """WIll be called by the ward"""
        assert (
            self.id
        ), "Cannot convert an object to a variable if you didn't query its unique id"
        return self.id


class GraphQLInputObject(BaseModel):
    def dict(self, *args, by_alias=True, **kwargs):

        return super().dict(
            *args,
            **{
                **kwargs,
                "by_alias": by_alias,
            },
        )

    async def to_variable(self):
        """WIll be called by the ward"""
        dictionary = self.dict(exclude={"typename"})
        clean_dict(dictionary, lambda key, value: key == "__typename" or value is None)
        return dictionary
