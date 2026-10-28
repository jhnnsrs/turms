"""The scopes a generated client needs, read off the directives of the root fields its operations use.

A server that says on each query, mutation and subscription which scope an app needs for it --
``createImage(...): Image! @auth(required_scopes: ["mikro_write"])`` -- lets the client know,
without anyone writing it down, which scopes the apps using it have to ask for. This plugin
walks every operation of the project, finds the root fields it selects (through fragments
spread or inlined on the root type as well), and emits what their directive asks for as one
list::

    SCOPES: List[str] = ["mikro_read", "mikro_write"]

It fails closed: a schema that does not declare the directive, or that cannot show where it is
applied (an introspected one carries no applications), is an error, never an empty list.
"""

import ast
from typing import Iterator, List, Optional

from graphql import (
    DirectiveNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLArgument,
    GraphQLSchema,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
    Undefined,
    value_from_ast,
)
from pydantic_settings import SettingsConfigDict

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.base import Plugin, PluginConfig
from turms.registry import ClassRegistry
from turms.schema_lookup import get_operation_root_type
from turms.utils import parse_documents


class ScopesPluginConfig(PluginConfig):
    model_config = SettingsConfigDict(env_prefix="TURMS_PLUGINS_SCOPES_")
    type: str = "turms.plugins.scopes.ScopesPlugin"
    directive: str = "auth"
    """The directive that says what a field needs."""
    arguments: List[str] = ["required_scopes"]
    """Its arguments whose values are scopes: each value given is gathered."""
    attribute: str = "SCOPES"
    """The name of the module-level list."""
    scopes_glob: Optional[str] = None
    """The documents to read, when not the project's own."""


def _root_fields(
    selection_set: SelectionSetNode,
    fragments: dict[str, FragmentDefinitionNode],
    seen: frozenset[str] = frozenset(),
) -> Iterator[FieldNode]:
    """The fields selected on the root type, through fragments spread or inlined on it."""
    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            yield selection
        elif isinstance(selection, InlineFragmentNode):
            yield from _root_fields(selection.selection_set, fragments, seen)
        elif isinstance(selection, FragmentSpreadNode):
            name = selection.name.value
            if name in seen or name not in fragments:
                continue
            yield from _root_fields(fragments[name].selection_set, fragments, seen | {name})


def _values(application: DirectiveNode, name: str, argument: GraphQLArgument) -> List[str]:
    node = next((a.value for a in application.arguments or () if a.name.value == name), None)
    if node is None:
        return []
    value = value_from_ast(node, argument.type)
    if value is Undefined:
        raise GenerationError(f"@{application.name.value}({name}: ...) is not a valid {argument.type}")
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


class ScopesPlugin(Plugin):
    config: ScopesPluginConfig = ScopesPluginConfig()

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        directive = client_schema.get_directive(self.config.directive)
        if directive is None:
            raise GenerationError(f"scopes: the schema declares no directive @{self.config.directive}")
        if directive.ast_node is None:
            raise GenerationError(
                f"scopes: @{self.config.directive} has no SDL definition, so where it is applied is "
                "invisible (an introspected schema carries none). Generate from the SDL the server prints."
            )
        unknown = [name for name in self.config.arguments if name not in directive.args]
        if unknown:
            raise GenerationError(f"scopes: @{self.config.directive} has no argument {', '.join(unknown)} (it has {sorted(directive.args)})")

        glob = self.config.scopes_glob or config.documents
        if not glob:
            raise GenerationError("scopes: no documents to read the operations from")
        documents = parse_documents(client_schema, glob, config)
        fragments = {d.name.value: d for d in documents.definitions if isinstance(d, FragmentDefinitionNode)}

        scopes: set[str] = set()
        for operation in documents.definitions:
            if not isinstance(operation, OperationDefinitionNode):
                continue
            root = get_operation_root_type(client_schema, operation)
            for field_node in _root_fields(operation.selection_set, fragments):
                field = root.fields.get(field_node.name.value)
                if field is None or field.ast_node is None:
                    continue
                for application in field.ast_node.directives or ():
                    if application.name.value != self.config.directive:
                        continue
                    for name in self.config.arguments:
                        scopes.update(_values(application, name, directive.args[name]))

        registry.register_import("typing.List")
        return [
            ast.AnnAssign(
                target=ast.Name(id=self.config.attribute, ctx=ast.Store()),
                annotation=ast.Subscript(value=ast.Name(id="List", ctx=ast.Load()), slice=ast.Name(id="str", ctx=ast.Load()), ctx=ast.Load()),
                value=ast.List(elts=[ast.Constant(value=scope) for scope in sorted(scopes)], ctx=ast.Load()),
                simple=1,
            )
        ]
