class SchemaClass:
    new_before_schema_field: str
    old_schema_field: str
    random_field: str
    new_after_schema_field: str

    def old_schema_call(x: str, new_parameter: str):
        # in old schema call comment

        return x


def schema_function(x: str) -> str:
    length = len(x)
    return None


def new_schema_function(x: str, t: int):
    pass
