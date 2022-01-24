import glob
import re
from typing import Dict, List
from turms.config import GeneratorConfig
from graphql.utilities.build_client_schema import GraphQLSchema
from graphql.language.ast import DocumentNode, FieldNode
from graphql.error.graphql_error import GraphQLError
from graphql import (
    language,
    parse,
    get_introspection_query,
    validate,
    build_client_schema,
)
import ast
from turms.globals import FRAGMENT_DOCUMENT_MAP, SCALAR_DEFAULTS


class FragmentNotFoundError(Exception):
    pass


class NoDocumentsFoundError(Exception):
    pass


class NoScalarEquivalentDefined(Exception):
    pass


def get_scalar_equivalent(scalar_type: str, config: GeneratorConfig):

    updated_dict = {**SCALAR_DEFAULTS, **config.scalar_definitions}

    try:
        scalar_type = updated_dict[scalar_type]
    except KeyError as e:
        raise NoScalarEquivalentDefined(
            f"No python equivalent found for {scalar_type}. Please define in scalar_definitions"
        )

    return scalar_type.split(".")[-1]


def target_from_node(node: FieldNode) -> str:
    return (
        node.alias.value if hasattr(node, "alias") and node.alias else node.name.value
    )


def build_schema(introspection_query: Dict[str, str]):
    return build_client_schema(introspection_query)


def generate_typename_field(typename):

    return ast.AnnAssign(
        target=ast.Name(id="typename", ctx=ast.Store()),
        annotation=ast.Subscript(
            value=ast.Name(id="Optional", ctx=ast.Load()),
            slice=ast.Subscript(
                value=ast.Name("Literal", ctx=ast.Load()),
                slice=ast.Constant(value=typename),
            ),
        ),
        value=ast.Call(
            func=ast.Name(id="Field", ctx=ast.Load()),
            args=[],
            keywords=[ast.keyword(arg="alias", value=ast.Constant(value="__typename"))],
        ),
        simple=1,
    )


def parse_documents(
    client_schema: GraphQLSchema, scan_glob="g/*/**.graphql"
) -> DocumentNode:
    """ """

    x = glob.glob(scan_glob, recursive=True)

    errors: List[GraphQLError] = []

    dsl = ""

    for file in x:
        with open(file, "r") as f:
            dsl += f.read()

    if dsl == "":
        raise NoDocumentsFoundError(
            f"Glob {scan_glob} did not find documents. Or only empty documents"
        )

    nodes = parse(dsl)

    errors = validate(client_schema, nodes)
    if len(errors) > 0:
        raise Exception(errors)

    return nodes


fragment_searcher = re.compile(r"\.\.\.(?P<fragment>[a-zA-Z]*)")


def replace_iteratively(pattern, taken=[]):
    z = fragment_searcher.findall(pattern)
    new_fragments = [new_f for new_f in z if new_f not in taken and new_f != ""]
    if not new_fragments:
        return pattern
    else:
        try:
            level_down_pattern = "\n\n".join(
                [FRAGMENT_DOCUMENT_MAP[key] for key in new_fragments] + [pattern]
            )
            return replace_iteratively(level_down_pattern, taken=new_fragments + taken)
        except KeyError as e:
            raise FragmentNotFoundError(
                f"Could not find in Fragment Map {FRAGMENT_DOCUMENT_MAP}"
            ) from e


def get_additional_bases_for_type(typename, config: GeneratorConfig):
    if typename in config.additional_bases:
        return [
            ast.Name(id=base.split(".")[-1], ctx=ast.Load())
            for base in config.additional_bases[typename]
        ]
    return []
