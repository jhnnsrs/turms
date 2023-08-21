import os
import json
from importlib import import_module
from typing import Any, Dict, Optional, Tuple
import glob
from pydantic import AnyHttpUrl
from turms.errors import GenerationError

from graphql import (
    get_introspection_query,
)

IntrospectionResult = Dict[str, Any]
DSLString = str


def import_class(module_path, class_name):
    """Import a module from a module_path and return the class"""
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


def generate_headers(
    default_headers: Dict[str, str], headers: Optional[Dict[str, str]]
) -> Dict[str, str]:
    """
    Generate headers for requests. It will combine the default_headers
    and headers dicts, and then also look for environment variables to
    create a final set of headers.

    For example:

    default_headers = {"Content-Type": "application/json"}
    headers = {"X-Hasura-Role": "admin"}
    # from the environment...
    os.environ["TURMS_HTTP_HEADERS"] = '{"Authorization": "Bearer 1234"}'

    will return...

    {
        "Content-Type": "application/json",
        "X-Hasura-Role": "admin",
        "Authorization": "Bearer 1234",
    }
    """

    final_headers = {**default_headers, **(headers or {})}

    if env_headers := os.environ.get("TURMS_HTTP_HEADERS"):
        final_headers.update(json.loads(env_headers))

    return final_headers


def load_introspection_from_url(
    url: AnyHttpUrl, headers: Optional[Dict[str, str]] = None
) -> IntrospectionResult:
    """Introspect a GraphQL schema using introspection query

    Args:
        schema_url (str): The Schema url
        bearer_token (str, optional): A Bearer token. Defaults to None.

    Raises:
        GenerationError: An error occurred while generating the schema.

    Returns:
        dict: The introspection query response.
    """
    try:  # pragma: no cover
        import requests  # pragma: no cover
    except ImportError:  # pragma: no cover
        raise GenerationError(
            "The requests library is required to introspect a schema from a url"
        )  # pragma: no cover

    jdata = json.dumps({"query": get_introspection_query()}).encode("utf-8")
    headers = generate_headers(
        {"Content-Type": "application/json", "Accept": "application/json"}, headers
    )
    try:
        req = requests.post(url, data=jdata, headers=headers)
        x = req.json()
    except Exception:
        raise GenerationError(f"Failed to fetch schema from {url}")
    if "errors" in x:  # pragma: no cover
        raise GenerationError(
            f"Failed to fetch schema from {url} Graphql error: {x['errors']}"
        )
    return x["data"]


def load_dsl_from_url(url: AnyHttpUrl, headers: Dict[str, str] = None) -> DSLString:
    try:  # pragma: no cover
        import requests  # pragma: no cover
    except ImportError:  # pragma: no cover
        raise GenerationError(
            "The requests library is required to introspect a schema from a url"
        )  # pragma: no cover

    headers = generate_headers({}, headers)
    try:
        req = requests.get(url, headers=headers)
        x = req.text()
    except Exception:
        raise GenerationError(f"Failed to fetch schema from {url}")
    return x


def load_dsl_from_file(file_path: str) -> DSLString:
    """Load a GraphQL DSL file and return its content as a string"""
    with open(file_path, "rb") as f:
        return f.read().decode("utf-8-sig")


def load_introspection_from_file(file_path: str) -> IntrospectionResult:
    """Load a GraphQL introspection file and return its content as a string"""
    with open(file_path, "rb") as f:
        return json.loads(f.read().decode("utf-8-sig"))


ParseResult = Tuple[Optional[DSLString], Optional[IntrospectionResult]]


def load_dsl_from_glob(
    glob_string: str,
    allow_introspection: bool = True,
) -> DSLString:
    """Build a GraphQL schema from a glob string"""
    schema_glob = glob.glob(glob_string, recursive=True)
    if len(schema_glob) == 0:
        raise GenerationError(f"No files found for glob string {glob_string}")

    dsl_string = ""
    for file in schema_glob:
        dsl_string += load_dsl_from_file(file)

    return dsl_string


def load_introspection_from_glob(
    glob_string: str,
):
    schema_glob = glob.glob(glob_string, recursive=True)
    if len(schema_glob) == 0:
        raise GenerationError(f"No files found for glob string {glob_string}")

    if len(schema_glob) > 1:
        raise GenerationError(
            f"More than one file found for glob string {glob_string}. Introspection can only be loaded from one file."
        )

    return load_introspection_from_file(schema_glob[0])
