from turms.types.object import GraphQLObject
from turms.types.object import GraphQLObject
from pydantic.fields import Field
from typing import Optional, List, Dict, Union, Literal
from enum import Enum
from turms.types.object import GraphQLObject
from turms.types.herre import GraphQLQuery
from turms.types.herre import GraphQLMutation
from turms.types.herre import GraphQLSubscription


class users_select_column(str, Enum):
    '''select columns of table "users"'''

    id = "id"
    "column name"
    name = "name"
    "column name"
    rocket = "rocket"
    "column name"
    timestamp = "timestamp"
    "column name"
    twitter = "twitter"
    "column name"


class order_by(str, Enum):
    """column ordering options"""

    asc = "asc"
    "in the ascending order, nulls last"
    asc_nulls_first = "asc_nulls_first"
    "in the ascending order, nulls first"
    asc_nulls_last = "asc_nulls_last"
    "in the ascending order, nulls last"
    desc = "desc"
    "in the descending order, nulls first"
    desc_nulls_first = "desc_nulls_first"
    "in the descending order, nulls first"
    desc_nulls_last = "desc_nulls_last"
    "in the descending order, nulls last"


class users_constraint(str, Enum):
    '''unique or primary key constraints on table "users"'''

    users_pkey = "users_pkey"
    "unique or primary key constraint"


class users_update_column(str, Enum):
    '''update columns of table "users"'''

    id = "id"
    "column name"
    name = "name"
    "column name"
    rocket = "rocket"
    "column name"
    timestamp = "timestamp"
    "column name"
    twitter = "twitter"
    "column name"


class conflict_action(str, Enum):
    """conflict action"""

    ignore = "ignore"
    "ignore the insert on this row"
    update = "update"
    "update the row with the given values"


class UserFragment(GraphQLObject):
    typename: Optional[Literal["users"]] = Field(alias="__typename")
    id: str


class UserQuery(GraphQLQuery):
    users: List[UserFragment]

    class Meta:
        domain = "default"
        document = "fragment User on users {\n  id\n}\n\nquery User {\n  users {\n    ...User\n  }\n}"


class TestqueryQueryCapsulesMissions(GraphQLObject):
    typename: Optional[Literal["CapsuleMission"]] = Field(alias="__typename")
    flight: Optional[int]


class TestqueryQueryCapsules(GraphQLObject):
    typename: Optional[Literal["Capsule"]] = Field(alias="__typename")
    id: Optional[str]
    missions: Optional[List[Optional[TestqueryQueryCapsulesMissions]]]


class TestqueryQuery(GraphQLQuery):
    capsules: Optional[List[Optional[TestqueryQueryCapsules]]]

    class Meta:
        domain = "default"
        document = "query TestQuery {\n  capsules {\n    id\n    missions {\n      flight\n    }\n  }\n}"


class TestmutationMutationInsert_usersReturning(GraphQLObject):
    '''columns and relationships of "users"'''

    typename: Optional[Literal["users"]] = Field(alias="__typename")
    id: str


class TestmutationMutationInsert_users(GraphQLObject):
    '''response of any mutation on the table "users"'''

    typename: Optional[Literal["users_mutation_response"]] = Field(alias="__typename")
    returning: List[TestmutationMutationInsert_usersReturning]
    "data of the affected rows by the mutation"


class TestmutationMutation(GraphQLMutation):
    insert_users: Optional[TestmutationMutationInsert_users]

    class Meta:
        domain = "default"
        document = "mutation TestMutation($id: uuid) {\n  insert_users(objects: {id: $id}) {\n    returning {\n      id\n    }\n  }\n}"


async def aUser() -> UserFragment:
    """User

    fetch data from the table: "users"

    Arguments:

    Returns:
        UserFragment: The returned Mutation"""
    return (await UserQuery.aexecute({})).users


def User() -> UserFragment:
    """User

    fetch data from the table: "users"

    Arguments:

    Returns:
        UserFragment: The returned Mutation"""
    return UserQuery.execute({}).users


async def aTestQuery() -> List[TestqueryQueryCapsules]:
    """TestQuery



    Arguments:

    Returns:
        TestqueryQueryCapsules: The returned Mutation"""
    return (await TestqueryQuery.aexecute({})).capsules


def TestQuery() -> List[TestqueryQueryCapsules]:
    """TestQuery



    Arguments:

    Returns:
        TestqueryQueryCapsules: The returned Mutation"""
    return TestqueryQuery.execute({}).capsules


async def aTestMutation(id: str = None) -> TestmutationMutationInsert_users:
    """TestMutation

    insert data into the table: "users"

    Arguments:
        id (uuid, Optional): uuid

    Returns:
        TestmutationMutationInsert_users: The returned Mutation"""
    return (await TestmutationMutation.aexecute({"id": id})).insert_users


def TestMutation(id: str = None) -> TestmutationMutationInsert_users:
    """TestMutation

    insert data into the table: "users"

    Arguments:
        id (uuid, Optional): uuid

    Returns:
        TestmutationMutationInsert_users: The returned Mutation"""
    return TestmutationMutation.execute({"id": id}).insert_users
