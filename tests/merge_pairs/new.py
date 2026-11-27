from enum import Enum


class SchemaClass:
    new_before_schema_field: str
    old_schema_field: str
    new_after_schema_field: str

    def old_schema_call(x: str, new_parameter: str):
        pass


def schema_function(x: str) -> str:
    pass


def new_schema_function(x: str, t: int):
    pass


class SchemaEnum(str, Enum):
    NEW_FIRST = "new_first"
    A = "A"
    NEW_LAST = "new_last"
