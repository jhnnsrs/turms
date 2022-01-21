from turms.types.object import GraphQLObject
from turms.types.object import GraphQLObject
from pydantic.fields import Field
from typing import Optional, List, Dict, Union, Literal
from enum import Enum
from turms.types.object import GraphQLObject
from turms.types.query import GraphQLQuery
from turms.types.mutation import GraphQLMutation
from turms.types.subscription import GraphQLSubscription


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


class JohannesQueryCapsulesMissions(GraphQLObject):
    typename: Optional[Literal["CapsuleMission"]] = Field(alias="__typename")
    flight: Optional[int]


class JohannesQueryCapsules(GraphQLObject):
    typename: Optional[Literal["Capsule"]] = Field(alias="__typename")
    id: Optional[str]
    missions: Optional[List[Optional[JohannesQueryCapsulesMissions]]]


class JohannesQuery(GraphQLQuery):
    capsules: Optional[List[Optional[JohannesQueryCapsules]]]

    class Meta:
        domain = "default"
        document = "query Johannes {\n  capsules {\n    id\n    missions {\n      flight\n    }\n  }\n}"


class InsertUserMutationInsert_usersReturning(GraphQLObject):
    typename: Optional[Literal["users"]] = Field(alias="__typename")
    id: str


class InsertUserMutationInsert_users(GraphQLObject):
    typename: Optional[Literal["users_mutation_response"]] = Field(alias="__typename")
    returning: List[InsertUserMutationInsert_usersReturning]
    "data of the affected rows by the mutation"


class InsertUserMutation(GraphQLMutation):
    insert_users: Optional[InsertUserMutationInsert_users]

    class Meta:
        domain = "default"
        document = "mutation InsertUser($id: uuid) {\n  insert_users(objects: {id: $id}) {\n    returning {\n      id\n    }\n  }\n}"


async def auseJohannes() -> JohannesQuery:
    """Query Johannes"""
    return await JohannesQuery.aquery({})


def useJohannes() -> JohannesQuery:
    """Query Johannes"""
    return JohannesQuery.query({})


async def auseInsertUser(id: str = None) -> InsertUserMutation:
    '''Query InsertUser


    insert_users: insert data into the table: "users"'''
    return await InsertUserMutation.aquery({"id": id})


def useInsertUser(id: str = None) -> InsertUserMutation:
    '''Query InsertUser


    insert_users: insert data into the table: "users"'''
    return InsertUserMutation.query({"id": id})
