from turms.types.object import GraphQLObject
from turms.types.object import GraphQLObject
from pydantic.fields import Field
from typing import Optional, List, Dict, Union, Literal
from enum import Enum
from turms.types.object import GraphQLInputObject
from turms.types.object import GraphQLObject
from turms.types.operation import GraphQLQuery
from turms.types.operation import GraphQLMutation
from turms.types.operation import GraphQLSubscription


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


class users_order_by(GraphQLInputObject):
    '''ordering options when selecting data from "users"'''

    id: Optional["order_by"]
    name: Optional["order_by"]
    rocket: Optional["order_by"]
    timestamp: Optional["order_by"]
    twitter: Optional["order_by"]


class users_bool_exp(GraphQLInputObject):
    """Boolean expression to filter rows from the table "users". All fields are combined with a logical 'AND'."""

    _and: Optional[List[Optional["users_bool_exp"]]]
    _not: Optional["users_bool_exp"]
    _or: Optional[List[Optional["users_bool_exp"]]]
    id: Optional["uuid_comparison_exp"]
    name: Optional["String_comparison_exp"]
    rocket: Optional["String_comparison_exp"]
    timestamp: Optional["timestamptz_comparison_exp"]
    twitter: Optional["String_comparison_exp"]


class uuid_comparison_exp(GraphQLInputObject):
    """expression to compare columns of type uuid. All fields are combined with logical 'AND'."""

    _eq: Optional[str]
    _gt: Optional[str]
    _gte: Optional[str]
    _in: Optional[List[str]]
    _is_null: Optional[bool]
    _lt: Optional[str]
    _lte: Optional[str]
    _neq: Optional[str]
    _nin: Optional[List[str]]


class String_comparison_exp(GraphQLInputObject):
    """expression to compare columns of type String. All fields are combined with logical 'AND'."""

    _eq: Optional[str]
    _gt: Optional[str]
    _gte: Optional[str]
    _ilike: Optional[str]
    _in: Optional[List[str]]
    _is_null: Optional[bool]
    _like: Optional[str]
    _lt: Optional[str]
    _lte: Optional[str]
    _neq: Optional[str]
    _nilike: Optional[str]
    _nin: Optional[List[str]]
    _nlike: Optional[str]
    _nsimilar: Optional[str]
    _similar: Optional[str]


class timestamptz_comparison_exp(GraphQLInputObject):
    """expression to compare columns of type timestamptz. All fields are combined with logical 'AND'."""

    _eq: Optional[str]
    _gt: Optional[str]
    _gte: Optional[str]
    _in: Optional[List[str]]
    _is_null: Optional[bool]
    _lt: Optional[str]
    _lte: Optional[str]
    _neq: Optional[str]
    _nin: Optional[List[str]]


class CapsulesFind(GraphQLInputObject):
    id: Optional[str]
    landings: Optional[int]
    mission: Optional[str]
    original_launch: Optional[str]
    reuse_count: Optional[int]
    status: Optional[str]
    type: Optional[str]


class CoresFind(GraphQLInputObject):
    asds_attempts: Optional[int]
    asds_landings: Optional[int]
    block: Optional[int]
    id: Optional[str]
    missions: Optional[str]
    original_launch: Optional[str]
    reuse_count: Optional[int]
    rtls_attempts: Optional[int]
    rtls_landings: Optional[int]
    status: Optional[str]
    water_landing: Optional[bool]


class HistoryFind(GraphQLInputObject):
    end: Optional[str]
    flight_number: Optional[int]
    id: Optional[str]
    start: Optional[str]


class LaunchFind(GraphQLInputObject):
    apoapsis_km: Optional[float]
    block: Optional[int]
    cap_serial: Optional[str]
    capsule_reuse: Optional[str]
    core_flight: Optional[int]
    core_reuse: Optional[str]
    core_serial: Optional[str]
    customer: Optional[str]
    eccentricity: Optional[float]
    end: Optional[str]
    epoch: Optional[str]
    fairings_recovered: Optional[str]
    fairings_recovery_attempt: Optional[str]
    fairings_reuse: Optional[str]
    fairings_reused: Optional[str]
    fairings_ship: Optional[str]
    gridfins: Optional[str]
    id: Optional[str]
    inclination_deg: Optional[float]
    land_success: Optional[str]
    landing_intent: Optional[str]
    landing_type: Optional[str]
    landing_vehicle: Optional[str]
    launch_date_local: Optional[str]
    launch_date_utc: Optional[str]
    launch_success: Optional[str]
    launch_year: Optional[str]
    legs: Optional[str]
    lifespan_years: Optional[float]
    longitude: Optional[float]
    manufacturer: Optional[str]
    mean_motion: Optional[float]
    mission_id: Optional[str]
    mission_name: Optional[str]
    nationality: Optional[str]
    norad_id: Optional[int]
    orbit: Optional[str]
    payload_id: Optional[str]
    payload_type: Optional[str]
    periapsis_km: Optional[float]
    period_min: Optional[float]
    raan: Optional[float]
    reference_system: Optional[str]
    regime: Optional[str]
    reused: Optional[str]
    rocket_id: Optional[str]
    rocket_name: Optional[str]
    rocket_type: Optional[str]
    second_stage_block: Optional[str]
    semi_major_axis_km: Optional[float]
    ship: Optional[str]
    side_core1_reuse: Optional[str]
    side_core2_reuse: Optional[str]
    site_id: Optional[str]
    site_name_long: Optional[str]
    site_name: Optional[str]
    start: Optional[str]
    tbd: Optional[str]
    tentative_max_precision: Optional[str]
    tentative: Optional[str]


class MissionsFind(GraphQLInputObject):
    id: Optional[str]
    manufacturer: Optional[str]
    name: Optional[str]
    payload_id: Optional[str]


class PayloadsFind(GraphQLInputObject):
    apoapsis_km: Optional[float]
    customer: Optional[str]
    eccentricity: Optional[float]
    epoch: Optional[str]
    inclination_deg: Optional[float]
    lifespan_years: Optional[float]
    longitude: Optional[float]
    manufacturer: Optional[str]
    mean_motion: Optional[float]
    nationality: Optional[str]
    norad_id: Optional[int]
    orbit: Optional[str]
    payload_id: Optional[str]
    payload_type: Optional[str]
    periapsis_km: Optional[float]
    period_min: Optional[float]
    raan: Optional[float]
    reference_system: Optional[str]
    regime: Optional[str]
    reused: Optional[bool]
    semi_major_axis_km: Optional[float]


class ShipsFind(GraphQLInputObject):
    id: Optional[str]
    name: Optional[str]
    model: Optional[str]
    type: Optional[str]
    role: Optional[str]
    active: Optional[bool]
    imo: Optional[int]
    mmsi: Optional[int]
    abs: Optional[int]
    class_: Optional[int] = Field(alias="class")
    weight_lbs: Optional[int]
    weight_kg: Optional[int]
    year_built: Optional[int]
    home_port: Optional[str]
    status: Optional[str]
    speed_kn: Optional[int]
    course_deg: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    successful_landings: Optional[int]
    attempted_landings: Optional[int]
    mission: Optional[str]


class users_insert_input(GraphQLInputObject):
    '''input type for inserting data into table "users"'''

    id: Optional[str]
    name: Optional[str]
    rocket: Optional[str]
    timestamp: Optional[str]
    twitter: Optional[str]


class users_on_conflict(GraphQLInputObject):
    '''on conflict condition type for table "users"'''

    constraint: "users_constraint"
    update_columns: List["users_update_column"]


class users_set_input(GraphQLInputObject):
    '''input type for updating data in table "users"'''

    id: Optional[str]
    name: Optional[str]
    rocket: Optional[str]
    timestamp: Optional[str]
    twitter: Optional[str]


class users_aggregate_order_by(GraphQLInputObject):
    '''order by aggregate values of table "users"'''

    count: Optional["order_by"]
    max: Optional["users_max_order_by"]
    min: Optional["users_min_order_by"]


class users_max_order_by(GraphQLInputObject):
    '''order by max() on columns of table "users"'''

    name: Optional["order_by"]
    rocket: Optional["order_by"]
    timestamp: Optional["order_by"]
    twitter: Optional["order_by"]


class users_min_order_by(GraphQLInputObject):
    '''order by min() on columns of table "users"'''

    name: Optional["order_by"]
    rocket: Optional["order_by"]
    timestamp: Optional["order_by"]
    twitter: Optional["order_by"]


class users_arr_rel_insert_input(GraphQLInputObject):
    '''input type for inserting array relation for remote table "users"'''

    data: List["users_insert_input"]
    on_conflict: Optional["users_on_conflict"]


class users_obj_rel_insert_input(GraphQLInputObject):
    '''input type for inserting object relation for remote table "users"'''

    data: "users_insert_input"
    on_conflict: Optional["users_on_conflict"]


users_bool_exp.update_forward_refs()
users_arr_rel_insert_input.update_forward_refs()
users_aggregate_order_by.update_forward_refs()
users_obj_rel_insert_input.update_forward_refs()


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
