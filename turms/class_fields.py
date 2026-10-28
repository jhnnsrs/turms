"""Class variables of generated classes, each declared as a policy.

A class field says four things: its ``name``, its ``kind`` (the annotation), the ``collector``
that gathers its values, and how those values ``combine`` into the one stamped::

    class_fields:                       # every class generated for a GraphQL type
      - name: __identifier__
        collector: {type: type_directive, directive: identified, argument: by}

    - type: turms.plugins.client.ClientPlugin
      client_fields:                    # the generated client class
        - name: __scopes__
          kind: tuple[str, ...]
          collector: {type: root_field_directive, directive: auth, argument: required_scopes}
          combine: union

A collector has a target: a ``type`` collector reads one GraphQL type (``class_fields`` stamps
every class generated for it), an ``operation`` collector reads one operation of a client
(``client_fields`` stamps the client class with what its operations gather). Each returns
*groups* -- one tuple of values per directive application, or per operation -- and the combine
turns them into the value::

    first         the first value                    a scalar
    all           every value, in order              a tuple
    ordered       every value once, first seen first a tuple
    union         every value once, sorted           a tuple
    intersection  the values every group holds       a tuple

or a dotted path to a function of the groups (then the field states its ``kind``). Without a
``kind`` the annotation is inferred: a single string, integer, boolean or enum value is its
``Literal`` (what lets a checker tell stamped classes apart), several are a tuple of the
values' type.

Directive applications are only visible in an SDL schema: a collector reading them refuses an
introspected one, as it refuses a directive or an argument the schema does not declare.
"""

from __future__ import annotations

import ast
import keyword
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, Iterator, List, Literal, Optional, Sequence, Tuple

from graphql import (
    DirectiveNode,
    FragmentDefinitionNode,
    GraphQLArgument,
    GraphQLNamedType,
    GraphQLSchema,
    OperationDefinitionNode,
    get_named_type,
)
from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator, model_validator

from turms.errors import GenerationError, RegistryError
from turms.helpers import import_string

if TYPE_CHECKING:
    from turms.registry import ClassRegistry

#: One tuple of values per directive application (a type collector) or per operation.
Groups = List[Tuple[object, ...]]
Combine = Callable[[Groups], object]
Target = Literal["type", "operation"]


# --- combines -----------------------------------------------------------------------------


def _sort_key(value: object) -> Tuple[str, object]:
    return (type(value).__name__, value if isinstance(value, (str, int, float, bool)) else repr(value))


def first(groups: Groups) -> object:
    """The first value of the first group."""
    return groups[0][0]


def all_values(groups: Groups) -> Tuple[object, ...]:
    """Every value, in order, duplicates kept."""
    return tuple(value for group in groups for value in group)


def ordered(groups: Groups) -> Tuple[object, ...]:
    """Every value once, the first seen first."""
    return tuple(dict.fromkeys(all_values(groups)))


def union(groups: Groups) -> Tuple[object, ...]:
    """Every value once, sorted."""
    return tuple(sorted(set(all_values(groups)), key=_sort_key))


def intersection(groups: Groups) -> Tuple[object, ...]:
    """The values every group holds, sorted."""
    if not groups:
        return ()
    common = set(groups[0]).intersection(*groups[1:])
    return tuple(sorted(common, key=_sort_key))


#: The combines a field can name, and whether each gives a scalar or a tuple.
COMBINES: Dict[str, Tuple[Combine, bool]] = {
    "first": (first, False),
    "all": (all_values, True),
    "ordered": (ordered, True),
    "union": (union, True),
    "intersection": (intersection, True),
}


# --- collectors ---------------------------------------------------------------------------


class Collector(BaseModel):
    """What gathers a class field's values. A ``type`` collector reads a GraphQL type, an
    ``operation`` collector an operation of a client."""

    model_config = ConfigDict(extra="forbid")

    type: str
    target: ClassVar[Target]

    @abstractmethod
    def check(self, schema: GraphQLSchema, registry: "ClassRegistry") -> None:
        """Refuse a schema this collector cannot read."""

    @abstractmethod
    def element_annotation(self, schema: GraphQLSchema, registry: "ClassRegistry") -> str:
        """The annotation of one value it collects."""

    @abstractmethod
    def default_combine(self, schema: GraphQLSchema) -> str:
        """The combine a field uses when it names none."""

    def collect_type(self, schema: GraphQLSchema, definition: GraphQLNamedType, registry: "ClassRegistry") -> Groups:
        """The groups ``definition`` contributes; empty when it says nothing."""
        raise NotImplementedError(f"{self.type} collects per operation, not per type")

    def collect_operation(
        self,
        schema: GraphQLSchema,
        operation: OperationDefinitionNode,
        fragments: Dict[str, FragmentDefinitionNode],
        registry: "ClassRegistry",
    ) -> Tuple[object, ...]:
        """The values one operation contributes."""
        raise NotImplementedError(f"{self.type} collects per type, not per operation")


def _values_of(value: object) -> Iterator[object]:
    """The values one argument holds: a list is its items, null is none."""
    if value is None:
        return
    if isinstance(value, (list, tuple)):
        yield from value
    else:
        yield value


class _DirectiveCollector(Collector):
    directive: str
    """The directive's name, without ``@``."""
    argument: Optional[str] = None
    """The argument whose value is collected; ``None`` collects ``True`` for presence."""

    #: Whether the applications it reads live in the schema (and so need its SDL).
    reads_schema: ClassVar[bool] = True

    def _argument(self, schema: GraphQLSchema, registry: "ClassRegistry") -> Optional[GraphQLArgument]:
        return registry.directive_definition(schema, self.directive, self.argument, needs_sdl=self.reads_schema)[1]

    def check(self, schema: GraphQLSchema, registry: "ClassRegistry") -> None:
        self._argument(schema, registry)

    def _applications(self, directives: Optional[Sequence[DirectiveNode]]) -> List[DirectiveNode]:
        return [application for application in directives or () if application.name.value == self.directive]


class TypeDirectiveCollector(_DirectiveCollector):
    """The directive's applications on a type: one group per application, holding the argument's
    value (an omitted argument takes the directive's default; no ``argument`` collects ``True``)."""

    type: str = "type_directive"
    target: ClassVar[Target] = "type"

    def element_annotation(self, schema: GraphQLSchema, registry: "ClassRegistry") -> str:
        from turms.registry import _class_var_annotation

        argument = self._argument(schema, registry)
        return _class_var_annotation(argument.type, registry) if argument is not None else "bool"

    def default_combine(self, schema: GraphQLSchema) -> str:
        directive = schema.get_directive(self.directive)
        return "all" if directive is not None and directive.is_repeatable else "first"

    def collect_type(self, schema: GraphQLSchema, definition: GraphQLNamedType, registry: "ClassRegistry") -> Groups:
        from turms.registry import _directive_argument_value

        node = definition.ast_node
        if node is None:
            return []
        argument = self._argument(schema, registry)
        nodes = [node, *(definition.extension_ast_nodes or ())]
        groups: Groups = []
        for application in (a for n in nodes for a in self._applications(getattr(n, "directives", None))):
            value = _directive_argument_value(application, self.argument, argument) if self.argument is not None and argument is not None else True
            groups.append((value,))
        return groups


class RootFieldDirectiveCollector(_DirectiveCollector):
    """The directive's argument on every root field an operation selects (through fragments
    spread or inlined on the root type), a list's items each one value. ``required``: a selected
    root field that does not give it fails generation, naming the field."""

    type: str = "root_field_directive"
    target: ClassVar[Target] = "operation"
    argument: str
    required: bool = True

    def element_annotation(self, schema: GraphQLSchema, registry: "ClassRegistry") -> str:
        from turms.registry import _class_var_annotation
        from graphql import GraphQLNonNull

        argument = self._argument(schema, registry)
        assert argument is not None
        return _class_var_annotation(GraphQLNonNull(get_named_type(argument.type)), registry)

    def default_combine(self, schema: GraphQLSchema) -> str:
        return "union"

    def collect_operation(
        self,
        schema: GraphQLSchema,
        operation: OperationDefinitionNode,
        fragments: Dict[str, FragmentDefinitionNode],
        registry: "ClassRegistry",
    ) -> Tuple[object, ...]:
        from turms.schema_lookup import get_operation_root_type, root_field_nodes

        argument = self._argument(schema, registry)
        assert argument is not None
        root = get_operation_root_type(schema, operation)
        values: List[object] = []
        for field_node in root_field_nodes(operation.selection_set, fragments):
            name = field_node.name.value
            field = root.fields.get(name)
            if field is None:
                continue  # __typename
            giving = [
                application
                for application in self._applications(field.ast_node.directives if field.ast_node is not None else None)
                if any(a.name.value == self.argument for a in application.arguments or ())
            ]
            if not giving and self.required:
                where = f"operation {operation.name.value}" if operation.name else "an anonymous operation"
                raise GenerationError(f"client_fields: {root.name}.{name} ({where}) gives no @{self.directive}({self.argument}: ...)")
            values.extend(value for application in giving for value in _values_of(_directive_value(application, self.argument, argument)))
        return tuple(values)


class OperationDirectiveCollector(_DirectiveCollector):
    """The directive's argument on the operation itself, in the client's own documents
    (``query GetImage @needs(scopes: ["x"])``), a list's items each one value."""

    type: str = "operation_directive"
    target: ClassVar[Target] = "operation"
    argument: str
    required: bool = False
    reads_schema: ClassVar[bool] = False

    def element_annotation(self, schema: GraphQLSchema, registry: "ClassRegistry") -> str:
        from turms.registry import _class_var_annotation
        from graphql import GraphQLNonNull

        argument = self._argument(schema, registry)
        assert argument is not None
        return _class_var_annotation(GraphQLNonNull(get_named_type(argument.type)), registry)

    def default_combine(self, schema: GraphQLSchema) -> str:
        return "union"

    def collect_operation(
        self,
        schema: GraphQLSchema,
        operation: OperationDefinitionNode,
        fragments: Dict[str, FragmentDefinitionNode],
        registry: "ClassRegistry",
    ) -> Tuple[object, ...]:
        argument = self._argument(schema, registry)
        assert argument is not None
        applications = self._applications(operation.directives)
        if not applications and self.required:
            where = operation.name.value if operation.name else "an anonymous operation"
            raise GenerationError(f"client_fields: {where} gives no @{self.directive}({self.argument}: ...)")
        return tuple(value for application in applications for value in _values_of(_directive_value(application, self.argument, argument)))


def _directive_value(application: DirectiveNode, name: str, argument: GraphQLArgument) -> object:
    from turms.registry import _directive_argument_value

    return _directive_argument_value(application, name, argument)


#: The collectors a field can name by a short ``type``; any other is a dotted path.
COLLECTORS: Dict[str, type] = {
    "type_directive": TypeDirectiveCollector,
    "root_field_directive": RootFieldDirectiveCollector,
    "operation_directive": OperationDirectiveCollector,
}


# --- the field ----------------------------------------------------------------------------

#: The names of ``typing`` a kind may use, and so the module they are imported from.
_TYPING_NAMES = {"Any", "Dict", "FrozenSet", "List", "Literal", "Optional", "Set", "Tuple", "Union"}
_LISTS = {"list", "List"}
_TUPLES = {"tuple", "Tuple"}
_SETS = {"set", "Set", "frozenset", "FrozenSet"}


def _outer(kind: ast.expr) -> str:
    node = kind.value if isinstance(kind, ast.Subscript) else kind
    return node.id if isinstance(node, ast.Name) else ""


class ClassField(BaseModel):
    """One class variable of a generated class: what it is called, what it is, what collects its
    values and how they combine (see the module)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    """The class variable's name. A dunder (``__identifier__``) never meets a field."""
    kind: Optional[str] = None
    """Its annotation (``tuple[str, ...]``); inferred from the collector and the combine when unset."""
    collector: Dict[str, Any]
    """What collects its values: ``type`` names a built-in (``type_directive``,
    ``root_field_directive``, ``operation_directive``) or a dotted path to a ``Collector``; the
    other keys are that collector's."""
    combine: Optional[str] = None
    """How the collected values become one: ``first``, ``all``, ``ordered``, ``union``,
    ``intersection``, or a dotted path. Unset: the collector's own default."""

    _collector: Collector = PrivateAttr()

    @field_validator("name")
    @classmethod
    def _is_an_identifier(cls, value: str) -> str:
        if not value.isidentifier() or keyword.iskeyword(value):
            raise ValueError(f"{value!r} is not a python identifier")
        return value

    @field_validator("kind")
    @classmethod
    def _is_an_annotation(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            try:
                ast.parse(value, mode="eval")
            except SyntaxError as error:
                raise ValueError(f"{value!r} is not a python annotation") from error
        return value

    @model_validator(mode="after")
    def _build(self) -> "ClassField":
        spec = dict(self.collector)
        kind = spec.get("type")
        if not isinstance(kind, str):
            raise ValueError("a collector says its `type`: a built-in name or a dotted path")
        collector_class = COLLECTORS.get(kind) or import_string(kind)
        if not (isinstance(collector_class, type) and issubclass(collector_class, Collector)):
            raise ValueError(f"{kind!r} is not a Collector")
        self._collector = collector_class.model_validate(spec)

        if self.combine is not None and self.combine not in COMBINES and self.kind is None:
            raise ValueError(f"{self.name}: a combine of your own ({self.combine}) needs the field's `kind`")
        if self.combine in COMBINES and self.kind is not None:
            sequence = COMBINES[self.combine][1]
            outer = _outer(ast.parse(self.kind, mode="eval").body)
            if sequence and outer not in _LISTS | _TUPLES | _SETS:
                raise ValueError(f"{self.name}: `{self.combine}` gives several values, but the kind {self.kind} holds one")
            if not sequence and outer in _LISTS | _TUPLES | _SETS:
                raise ValueError(f"{self.name}: `{self.combine}` gives one value, but the kind {self.kind} holds several")
        return self

    @property
    def collector_instance(self) -> Collector:
        return self._collector

    def combine_function(self, schema: GraphQLSchema) -> Tuple[Combine, Optional[bool]]:
        """The combine to use, and whether it gives a tuple (``None``: one of your own)."""
        name = self.combine or self._collector.default_combine(schema)
        if name in COMBINES:
            return COMBINES[name]
        return import_string(name), None

    def stamp(self, groups: Groups, schema: GraphQLSchema, registry: "ClassRegistry") -> Tuple[str, str, str]:
        """``(name, annotation, value source)`` of the class variable these groups make."""
        combine, sequence = self.combine_function(schema)
        if sequence is False and not groups:
            raise GenerationError(f"{self.name}: nothing was collected for `{self.combine or 'first'}` to take")
        value = combine(groups)
        if self.kind is None:
            element = self._collector.element_annotation(schema, registry)
            if sequence:
                registry.register_import("typing.Tuple")
                return self.name, f"Tuple[{element}, ...]", repr(_items(self.name, value))
            return self.name, registry._literal_or(element, value), repr(value)

        parsed = ast.parse(self.kind, mode="eval").body
        for node in ast.walk(parsed):
            if isinstance(node, ast.Name) and node.id in _TYPING_NAMES:
                registry.register_import(f"typing.{node.id}")
        outer = _outer(parsed)
        if outer in _LISTS:
            source = repr(list(_items(self.name, value)))
        elif outer in _TUPLES:
            source = repr(_items(self.name, value))
        elif outer in _SETS:
            # Spelled out in the combined order: a set's own repr changes with the hash seed.
            items = ", ".join(repr(item) for item in _items(self.name, value))
            source = f"frozenset({{{items}}})" if items else "frozenset()"
        else:
            source = repr(value)
        return self.name, self.kind, source


def _items(name: str, value: object) -> Tuple[object, ...]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(value)
    raise GenerationError(f"{name}: the combine gave {value!r}, but the field holds several values")


def check_target(field: ClassField, target: Target, where: str) -> Collector:
    """The field's collector, refused when it reads something else than ``where`` stamps."""
    collector = field.collector_instance
    if collector.target != target:
        raise RegistryError(
            f"{where}: {field.name} is collected per {collector.target} ({collector.type}), but {where} stamps per {target}"
        )
    return collector


__all__ = [
    "COLLECTORS",
    "COMBINES",
    "ClassField",
    "Collector",
    "Groups",
    "OperationDirectiveCollector",
    "RootFieldDirectiveCollector",
    "TypeDirectiveCollector",
    "check_target",
]
