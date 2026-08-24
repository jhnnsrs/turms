"""Rewrites the generated annotations into their modern spelling.

Plugins always build annotations in the classic ``typing`` style
(``typing.Optional[typing.List[X]]``). Rather than teaching every plugin about
both spellings, the whole generated tree is rewritten once, right after the
plugins ran, according to :class:`turms.config.GeneratorConfig`:

- PEP 585 (python 3.9): ``typing.List[X]`` -> ``list[X]``
- PEP 604 (python 3.10): ``typing.Optional[X]`` -> ``X | None`` and
  ``typing.Union[A, B]`` -> ``A | B``

Only the two thresholds above change what turms emits; the modern typing
features of 3.11+ (``Self``, ``NotRequired``, PEP 695 ``type``) never appear in
generated code, so there is nothing to switch on for them.
"""

import ast
from typing import Dict, List, Set

from turms.config import GeneratorConfig
from turms.registry import ClassRegistry

BUILTIN_GENERICS: Dict[str, str] = {
    "List": "list",
    "Dict": "dict",
    "Tuple": "tuple",
    "Set": "set",
    "FrozenSet": "frozenset",
    "Type": "type",
}
"""``typing`` aliases that PEP 585 replaced with the builtin they shadow."""

UNION_ALIASES = ("Optional", "Union")


def _is_forward_ref(node: ast.expr) -> bool:
    """A bare string annotation (a forward reference like ``'Country'``).

    Such a node cannot become an operand of ``|`` -- ``'Country' | None`` raises
    a TypeError while the class body is evaluated -- so a union containing one
    has to be emitted as a string annotation instead.
    """
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _union_of(elements: List[ast.expr]) -> ast.expr:
    """Builds ``a | b | c`` from the given operands.

    If any operand is a forward reference the whole union is emitted as a single
    string annotation (``'Country | None'``), which pydantic resolves on
    ``model_rebuild()``.
    """
    if len(elements) == 1:
        return elements[0]

    if any(_is_forward_ref(element) for element in elements):
        source = " | ".join(
            element.value if _is_forward_ref(element) else ast.unparse(element)
            for element in elements
        )
        return ast.Constant(value=source)

    node = elements[0]
    for element in elements[1:]:
        node = ast.BinOp(left=node, op=ast.BitOr(), right=element)
    return node


class AnnotationModernizer(ast.NodeTransformer):
    """Rewrites classic ``typing`` annotations into their modern equivalent.

    ``eligible`` limits the rewrite to names that really came from ``typing`` --
    a user can point ``scalar_definitions`` at their own ``mymodule.List``, and
    that must not be turned into the builtin.
    """

    def __init__(
        self, eligible: Set[str], builtin_generics: bool, union_operator: bool
    ):
        self.eligible = eligible
        self.builtin_generics = builtin_generics
        self.union_operator = union_operator

    def _visit_sequence(self, values: list) -> list:
        visited = []
        for value in values:
            if isinstance(value, list):
                # Plugins occasionally nest a list of statements inside a body.
                # ast.unparse flattens those, so they have to be traversed too.
                visited.append(self._visit_sequence(value))
            elif isinstance(value, ast.AST):
                visited.append(self.visit(value))
            else:
                visited.append(value)
        return visited

    def generic_visit(self, node: ast.AST) -> ast.AST:
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                setattr(node, field, self._visit_sequence(value))
            elif isinstance(value, ast.AST):
                setattr(node, field, self.visit(value))
        return node

    def visit_Subscript(self, node: ast.Subscript) -> ast.expr:
        node = self.generic_visit(node)

        if not self.union_operator or not isinstance(node.value, ast.Name):
            return node

        name = node.value.id
        if name not in self.eligible or name not in UNION_ALIASES:
            return node

        elements = (
            list(node.slice.elts) if isinstance(node.slice, ast.Tuple) else [node.slice]
        )
        if name == "Optional":
            elements = elements + [ast.Constant(value=None)]

        return _union_of(elements)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        # Catches both the `List` of a `List[X]` subscript and bare references,
        # e.g. a `GenericScalar: typing.Dict` scalar definition.
        if self.builtin_generics and node.id in self.eligible:
            builtin = BUILTIN_GENERICS.get(node.id)
            if builtin:
                return ast.Name(id=builtin, ctx=node.ctx)
        return node


def _eligible_names(registry: ClassRegistry, config: GeneratorConfig) -> Set[str]:
    """The typing names that may be rewritten.

    A name is eligible when it was registered as a ``typing`` import and is not
    shadowed by an import from any other module.
    """
    candidates = set(BUILTIN_GENERICS if config.use_builtin_generics else ())
    if config.use_union_operator:
        candidates |= set(UNION_ALIASES)

    imports = registry.registered_imports
    from_typing = {
        name.split(".")[-1] for name in imports if name.startswith("typing.")
    }
    shadowed = {
        name.split(".")[-1] for name in imports if not name.startswith("typing.")
    }
    return (candidates & from_typing) - shadowed


def _walk(node) -> "list":
    """``ast.walk`` that also descends into nested lists (see ``_visit_sequence``)."""
    nodes = []
    if isinstance(node, list):
        for item in node:
            nodes.extend(_walk(item))
    elif isinstance(node, ast.AST):
        nodes.append(node)
        for _, value in ast.iter_fields(node):
            nodes.extend(_walk(value))
    return nodes


def _used_names(tree: List[ast.AST]) -> Set[str]:
    return {node.id for node in _walk(tree) if isinstance(node, ast.Name)}


def modernize_annotations(
    tree: List[ast.AST],
    config: GeneratorConfig,
    registry: ClassRegistry,
) -> List[ast.AST]:
    """Rewrites ``tree`` in place-ish and drops the typing imports it made obsolete.

    Must run before ``registry.generate_imports()`` so the pruned imports never
    make it into the output.
    """
    if not config.use_builtin_generics and not config.use_union_operator:
        return tree

    eligible = _eligible_names(registry, config)
    if not eligible:
        return tree

    modernizer = AnnotationModernizer(
        eligible,
        builtin_generics=config.use_builtin_generics,
        union_operator=config.use_union_operator,
    )
    tree = [modernizer.visit(node) for node in tree]

    # Keep an import as long as anything still references the name -- plugins we
    # do not know about may have emitted it in a spot we did not rewrite.
    still_used = _used_names(tree) | _used_names(registry.generate_builtins())
    for name in eligible - still_used:
        registry.unregister_import(f"typing.{name}")

    return tree


def optional_label(label: str, config: GeneratorConfig) -> str:
    """Spells an optional type for the human readable docstrings."""
    if config.use_union_operator:
        return f"{label} | None"
    return f"Optional[{label}]"


def list_label(label: str, config: GeneratorConfig) -> str:
    """Spells a list type for the human readable docstrings."""
    if config.use_builtin_generics:
        return f"list[{label}]"
    return f"List[{label}]"
