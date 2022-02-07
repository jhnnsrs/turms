from turms.types.operation import GraphQLMutation, GraphQLQuery
from turms.types.object import GraphQLInputObject, GraphQLObject
from enum import Enum
from typing import List, Literal, Optional
from pydantic import Field


class Users_select_column(str, Enum):
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


class Order_by(str, Enum):
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


class Users_constraint(str, Enum):
    '''unique or primary key constraints on table "users"'''

    users_pkey = "users_pkey"
    "unique or primary key constraint"


class Users_update_column(str, Enum):
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


class Conflict_action(str, Enum):
    """conflict action"""

    ignore = "ignore"
    "ignore the insert on this row"
    update = "update"
    "update the row with the given values"


class Users_order_by(GraphQLInputObject):
    '''ordering options when selecting data from "users"'''

    id: Optional["Order_by"]
    name: Optional["Order_by"]
    rocket: Optional["Order_by"]
    timestamp: Optional["Order_by"]
    twitter: Optional["Order_by"]


class Users_bool_exp(GraphQLInputObject):
    """Boolean expression to filter rows from the table "users". All fields are combined with a logical 'AND'."""

    _and: Optional[List[Optional["Users_bool_exp"]]]
    _not: Optional["Users_bool_exp"]
    _or: Optional[List[Optional["Users_bool_exp"]]]
    id: Optional["Uuid_comparison_exp"]
    name: Optional["String_comparison_exp"]
    rocket: Optional["String_comparison_exp"]
    timestamp: Optional["Timestamptz_comparison_exp"]
    twitter: Optional["String_comparison_exp"]


class Uuid_comparison_exp(GraphQLInputObject):
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


class Timestamptz_comparison_exp(GraphQLInputObject):
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


class Capsulesfind(GraphQLInputObject):
    id: Optional[str]
    landings: Optional[int]
    mission: Optional[str]
    original_launch: Optional[str]
    reuse_count: Optional[int]
    status: Optional[str]
    type: Optional[str]


class Coresfind(GraphQLInputObject):
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


class Historyfind(GraphQLInputObject):
    end: Optional[str]
    flight_number: Optional[int]
    id: Optional[str]
    start: Optional[str]


class Launchfind(GraphQLInputObject):
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


class Missionsfind(GraphQLInputObject):
    id: Optional[str]
    manufacturer: Optional[str]
    name: Optional[str]
    payload_id: Optional[str]


class Payloadsfind(GraphQLInputObject):
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


class Shipsfind(GraphQLInputObject):
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


class Users_insert_input(GraphQLInputObject):
    '''input type for inserting data into table "users"'''

    id: Optional[str]
    name: Optional[str]
    rocket: Optional[str]
    timestamp: Optional[str]
    twitter: Optional[str]


class Users_on_conflict(GraphQLInputObject):
    '''on conflict condition type for table "users"'''

    constraint: "Users_constraint"
    update_columns: List["Users_update_column"]


class Users_set_input(GraphQLInputObject):
    '''input type for updating data in table "users"'''

    id: Optional[str]
    name: Optional[str]
    rocket: Optional[str]
    timestamp: Optional[str]
    twitter: Optional[str]


class Users_aggregate_order_by(GraphQLInputObject):
    '''order by aggregate values of table "users"'''

    count: Optional["Order_by"]
    max: Optional["Users_max_order_by"]
    min: Optional["Users_min_order_by"]


class Users_max_order_by(GraphQLInputObject):
    '''order by max() on columns of table "users"'''

    name: Optional["Order_by"]
    rocket: Optional["Order_by"]
    timestamp: Optional["Order_by"]
    twitter: Optional["Order_by"]


class Users_min_order_by(GraphQLInputObject):
    '''order by min() on columns of table "users"'''

    name: Optional["Order_by"]
    rocket: Optional["Order_by"]
    timestamp: Optional["Order_by"]
    twitter: Optional["Order_by"]


class Users_arr_rel_insert_input(GraphQLInputObject):
    '''input type for inserting array relation for remote table "users"'''

    data: List["Users_insert_input"]
    on_conflict: Optional["Users_on_conflict"]


class Users_obj_rel_insert_input(GraphQLInputObject):
    '''input type for inserting object relation for remote table "users"'''

    data: "Users_insert_input"
    on_conflict: Optional["Users_on_conflict"]


Users_bool_exp.update_forward_refs()
Users_arr_rel_insert_input.update_forward_refs()
Users_aggregate_order_by.update_forward_refs()
Users_obj_rel_insert_input.update_forward_refs()


class User(GraphQLObject):
    typename: Optional[Literal["users"]] = Field(alias="__typename")
    id: str


class User(GraphQLQuery):
    users: List[User]

    class Meta:
        domain = "default"
        document = "User\n\nquery User {\n  users {\n    ...User\n  }\n}"


class TestqueryCapsulesMissions(GraphQLObject):
    typename: Optional[Literal["CapsuleMission"]] = Field(alias="__typename")
    flight: Optional[int]


class TestqueryCapsules(GraphQLObject):
    typename: Optional[Literal["Capsule"]] = Field(alias="__typename")
    id: Optional[str]
    missions: Optional[List[Optional[TestqueryCapsulesMissions]]]


class Testquery(GraphQLQuery):
    capsules: Optional[List[Optional[TestqueryCapsules]]]

    class Meta:
        domain = "default"
        document = "query TestQuery {\n  capsules {\n    id\n    missions {\n      flight\n    }\n  }\n}"


class TestmutationInsert_usersReturning(GraphQLObject):
    '''columns and relationships of "users"'''

    typename: Optional[Literal["users"]] = Field(alias="__typename")
    id: str


class TestmutationInsert_users(GraphQLObject):
    '''response of any mutation on the table "users"'''

    typename: Optional[Literal["users_mutation_response"]] = Field(alias="__typename")
    returning: List[TestmutationInsert_usersReturning]
    "data of the affected rows by the mutation"


class Testmutation(GraphQLMutation):
    insert_users: Optional[TestmutationInsert_users]

    class Meta:
        domain = "default"
        document = "mutation TestMutation($id: uuid) {\n  insert_users(objects: {id: $id}) {\n    returning {\n      id\n    }\n  }\n}"


async def aUser() -> User:
    """User

    fetch data from the table: "users"

    Arguments:

    Returns:
        User: The returned Mutation"""
    return (await User.aexecute({})).users


def User() -> User:
    """User

    fetch data from the table: "users"

    Arguments:

    Returns:
        User: The returned Mutation"""
    return User.execute({}).users


async def aTestQuery() -> List[TestqueryCapsules]:
    """TestQuery



    Arguments:

    Returns:
        TestqueryCapsules: The returned Mutation"""
    return (await Testquery.aexecute({})).capsules


def TestQuery() -> List[TestqueryCapsules]:
    """TestQuery



    Arguments:

    Returns:
        TestqueryCapsules: The returned Mutation"""
    return Testquery.execute({}).capsules


async def aTestMutation(id: str = None) -> TestmutationInsert_users:
    """TestMutation

    insert data into the table: "users"

    Arguments:
        id (uuid, Optional): uuid

    Returns:
        TestmutationInsert_users: The returned Mutation"""
    return (await Testmutation.aexecute({"id": id})).insert_users


def TestMutation(id: str = None) -> TestmutationInsert_users:
    """TestMutation

    insert data into the table: "users"

    Arguments:
        id (uuid, Optional): uuid

    Returns:
        TestmutationInsert_users: The returned Mutation"""
    return Testmutation.execute({"id": id}).insert_users
