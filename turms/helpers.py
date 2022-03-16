import json
from importlib import import_module
from typing import Optional
from urllib import request
import glob
import graphql
from turms.errors import GenerationError

from graphql import (
    build_ast_schema,
    build_client_schema,
    get_introspection_query,
    parse,
)


def import_class(module_path, class_name):
    module = import_module(module_path)
    return getattr(module, class_name)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed. Simliar to
    djangos import_string, but without the cache.
    """

    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from err

    try:
        return import_class(module_path, class_name)
    except AttributeError as err:
        raise ImportError(
            f"{module_path} does not define a {class_name} attribute/class"
        ) from err


def build_schema_from_introspect_url(
    schema_url: str, bearer_token: Optional[str] = None
) -> graphql.GraphQLSchema:
    """Introspect a GraphQL schema using introspection query

    Args:
        schema_url (_type_): The Schema url
        bearer_token (_type_, optional): A Bearer token. Defaults to None.

    Raises:
        GenerationError: _description_

    Returns:
        _type_: _description_
    """
    jdata = json.dumps({"query": get_introspection_query()}).encode("utf-8")
    req = request.Request(schema_url, data=jdata)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if bearer_token:
        req.add_header("Authorization", f"Bearer {bearer_token}")

    try:
        resp = request.urlopen(req)
        x = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise GenerationError(f"Failed to fetch schema from {schema_url}")

    if "errors" in x:
        raise GenerationError(
            f"Failed to fetch schema from {schema_url} Graphql error: {x['errors']}"
        )

    return build_client_schema(x["data"])


def build_schema_from_glob(glob_string: str):
    """Build a GraphQL schema from a glob string"""
    schema_glob = glob.glob(glob_string, recursive=True)
    dsl_string = ""
    introspection_string = ""
    for file in schema_glob:
        with open(file, "r") as f:
            if file.endswith(".graphql"):
                dsl_string += f.read()
            elif file.endswith(".json"):
                # not really necessary as json files are generally not splitable
                introspection_string += f.read

    if not dsl_string and not introspection_string:
        raise GenerationError(f"No schema files found in {glob_string}")

    if dsl_string != "" and introspection_string != "":
        raise GenerationError("We cannot have both dsl and introspection files")
    if dsl_string != "":
        return build_ast_schema(parse(dsl_string))
    else:
        return build_client_schema(json.loads(introspection_string))
