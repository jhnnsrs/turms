"""One class whose methods are the operations of the API.

The generated class is a mixin. Each method builds the operation's variables and
hands the operation class and them to a method of ``self``: ``execute`` and
``aexecute`` for queries and mutations, ``subscribe`` and ``asubscribe`` for
subscriptions (the names are configurable). The generated module imports no
executor; those four come from the class the mixin is mixed into, or from one of
``client_bases``.
"""

from __future__ import annotations

import ast
import importlib
from typing import List, Optional

from graphql import GraphQLSchema
from graphql.language.ast import OperationDefinitionNode, OperationType
from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.base import Plugin
from turms.plugins.funcs import (
    NO_EXTRAS,
    OperationFuncsConfig,
    generate_async_func_name,
    generate_document_arg,
    generate_parameters,
    generate_passing_extra_args_for_onode,
    generate_passing_extra_kwargs_for_onode,
    generate_query_doc,
    generate_sync_func_name,
    generate_variable_assignments,
    get_return_type_annotation,
    is_collapsable,
)
from turms.registry import ClassRegistry
from turms.utils import parse_documents


class ClientPluginConfig(OperationFuncsConfig):
    model_config = SettingsConfigDict(
        extra="forbid", env_prefix="TURMS_PLUGINS_CLIENT_"
    )
    type: str = "turms.plugins.client.ClientPlugin"
    client_class: str
    """The name of the generated class."""
    client_bases: List[str] = []
    """Dotted paths of the bases of the generated class. A base that implements
    the delegate methods makes the class usable on its own."""
    documents: Optional[str] = None
    """A glob of the documents to generate methods for; the project's documents
    by default."""
    sync_methods: bool = True
    """Generate a blocking method per operation (named with ``prepend_sync``)."""
    async_methods: bool = True
    """Generate an awaitable method per operation (named with ``prepend_async``)."""
    execute: str = "execute"
    """The method of ``self`` a blocking query or mutation calls, as
    ``self.execute(Operation, variables)``; it returns the operation model."""
    aexecute: str = "aexecute"
    """The method of ``self`` an awaitable query or mutation awaits, as
    ``await self.aexecute(Operation, variables)``; it returns the operation model."""
    subscribe: str = "subscribe"
    """The method of ``self`` a blocking subscription iterates, as
    ``for event in self.subscribe(Operation, variables)``; it yields operation
    models."""
    asubscribe: str = "asubscribe"
    """The method of ``self`` an awaitable subscription iterates, as
    ``async for event in self.asubscribe(Operation, variables)``; it yields
    operation models."""
    reserved_names: List[str] = []
    """Names the generated class must not define (e.g. fields of the class it is
    mixed into). An operation whose method would take one of them is an error."""
    reserved_from: List[str] = []
    """Dotted paths of classes the generated class will be mixed into. Every
    attribute they have (and every pydantic field they declare) is reserved:
    pydantic lets a field silently hide a same-named method, with only a warning."""

    @model_validator(mode="after")
    def _check(self) -> "ClientPluginConfig":
        if not self.client_class.isidentifier():
            raise ValueError(
                f"client_class must be an identifier, got {self.client_class!r}"
            )
        for delegate in self.delegates:
            if not delegate.isidentifier():
                raise ValueError(
                    f"delegate method names must be identifiers, got {delegate!r}"
                )
        if not (self.sync_methods or self.async_methods):
            raise ValueError(
                "at least one of sync_methods and async_methods must be on"
            )
        return self

    @property
    def delegates(self) -> set[str]:
        """The names of the methods of ``self`` the generated methods call."""
        return {self.execute, self.aexecute, self.subscribe, self.asubscribe}

    def delegate_for(self, operation: OperationType, is_async: bool) -> str:
        if operation == OperationType.SUBSCRIPTION:
            return self.asubscribe if is_async else self.subscribe
        return self.aexecute if is_async else self.execute


def names_reserved_by(
    dotted_paths: List[str], generated: str | None = None
) -> set[str]:
    """Every attribute and pydantic field name of the given classes.

    Attributes a class only has through a base named ``generated`` are skipped:
    that base is the class being generated, so once a client mixes it in, its
    own previous output must not reserve the names it is about to emit again.
    """
    names: set[str] = set()
    for path in dotted_paths:
        module_name, _, cls_name = path.rpartition(".")
        cls = getattr(importlib.import_module(module_name), cls_name)
        for klass in cls.__mro__:
            if generated is not None and klass.__name__ == generated:
                continue
            names |= set(vars(klass))
        names |= set(getattr(cls, "model_fields", {}) or {})
    return names


def generate_delegate_call(
    o: OperationDefinitionNode,
    is_async: bool,
    plugin_config: ClientPluginConfig,
    registry: ClassRegistry,
) -> ast.Call:
    """``self.<delegate>(<Operation>, variables, ...)``"""
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="self", ctx=ast.Load()),
            attr=plugin_config.delegate_for(o.operation, is_async),
            ctx=ast.Load(),
        ),
        args=generate_passing_extra_args_for_onode(NO_EXTRAS, plugin_config)
        + [
            generate_document_arg(o, registry),
            ast.Name(id="variables", ctx=ast.Load()),
        ],
        keywords=generate_passing_extra_kwargs_for_onode(NO_EXTRAS, plugin_config),
    )


def collapsed_field(o: OperationDefinitionNode, registry: ClassRegistry) -> str:
    field = o.selection_set.selections[0]
    return registry.generate_node_name(
        field.alias.value if field.alias else field.name.value
    )


def generate_delegation(
    o: OperationDefinitionNode,
    is_async: bool,
    collapse: bool,
    plugin_config: ClientPluginConfig,
    registry: ClassRegistry,
) -> ast.stmt:
    """The statement that hands the operation to ``self`` and returns its result."""
    call = generate_delegate_call(o, is_async, plugin_config, registry)

    def unwrap(value: ast.expr) -> ast.expr:
        if not collapse:
            return value
        return ast.Attribute(
            value=value, attr=collapsed_field(o, registry), ctx=ast.Load()
        )

    if o.operation != OperationType.SUBSCRIPTION:
        result: ast.expr = ast.Await(value=call) if is_async else call
        return ast.Return(value=unwrap(result))

    loop = ast.AsyncFor if is_async else ast.For
    return loop(
        target=ast.Name(id="event", ctx=ast.Store()),
        iter=call,
        body=[
            ast.Expr(
                value=ast.Yield(value=unwrap(ast.Name(id="event", ctx=ast.Load())))
            )
        ],
        orelse=[],
    )


def generate_method(
    o: OperationDefinitionNode,
    is_async: bool,
    client_schema: GraphQLSchema,
    config: GeneratorConfig,
    plugin_config: ClientPluginConfig,
    registry: ClassRegistry,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    collapse = plugin_config.collapse_lonely and is_collapsable(o)

    return_type = get_return_type_annotation(
        o, client_schema, registry, collapse=collapse
    )
    if o.operation == OperationType.SUBSCRIPTION:
        iterator = "AsyncIterator" if is_async else "Iterator"
        registry.register_import(f"typing.{iterator}")
        return_type = ast.Subscript(
            value=ast.Name(id=iterator, ctx=ast.Load()), slice=return_type
        )

    parameters = generate_parameters(
        NO_EXTRAS, o, config, plugin_config, registry, client_schema
    )
    parameters.args.insert(0, ast.arg(arg="self"))

    body = [
        generate_query_doc(
            NO_EXTRAS, o, client_schema, config, plugin_config, registry, collapse
        ),
        *generate_variable_assignments(o, plugin_config, registry, client_schema),
        generate_delegation(o, is_async, collapse, plugin_config, registry),
    ]

    if is_async:
        return ast.AsyncFunctionDef(
            name=generate_async_func_name(o, plugin_config, config, registry),
            args=parameters,
            body=body,
            decorator_list=[],
            returns=return_type,
        )
    return ast.FunctionDef(
        name=generate_sync_func_name(o, plugin_config, config, registry),
        args=parameters,
        body=body,
        decorator_list=[],
        returns=return_type,
    )


def generate_client_class(
    methods: List[ast.FunctionDef | ast.AsyncFunctionDef],
    plugin_config: ClientPluginConfig,
    registry: ClassRegistry,
) -> ast.ClassDef:
    """Wraps the generated methods in the client class.

    Refuses a method that would shadow a reserved name or a delegate, a
    parameter named ``self``, and two methods with one name: inside a class the
    second would silently win.
    """
    reserved = (
        set(plugin_config.reserved_names)
        | names_reserved_by(plugin_config.reserved_from, plugin_config.client_class)
        | plugin_config.delegates
        | {"self"}
    )
    seen: set[str] = set()

    for method in methods:
        if method.name in reserved:
            raise GenerationError(
                f"Generated method {method.name!r} on {plugin_config.client_class} "
                "shadows a reserved name; rename the operation"
            )
        if method.name in seen:
            raise GenerationError(
                f"Two operations generate the method {method.name!r} on "
                f"{plugin_config.client_class}"
            )
        seen.add(method.name)
        for arg in method.args.args[1:]:
            if arg.arg == "self":
                raise GenerationError(
                    f"Operation {method.name!r} has a variable named 'self', which "
                    "cannot be a method parameter; rename the variable"
                )

    bases = []
    for base in plugin_config.client_bases:
        registry.register_import(base)
        bases.append(ast.Name(id=base.split(".")[-1], ctx=ast.Load()))

    delegates = ", ".join(
        f"``{name}``"
        for name in (
            plugin_config.execute,
            plugin_config.aexecute,
            plugin_config.subscribe,
            plugin_config.asubscribe,
        )
    )
    doc = ast.Expr(
        value=ast.Constant(
            value=(
                "Every operation of this API as a method. Generated by turms.\n\n"
                f"Each method hands its operation to {delegates} of ``self``, which "
                "the class this one is mixed into (or a base of it) provides."
            )
        )
    )

    return ast.ClassDef(
        name=plugin_config.client_class,
        bases=bases,
        keywords=[],
        body=[doc, *methods],
        decorator_list=[],
        type_params=[],
    )


class ClientPlugin(Plugin):
    """Generates one class whose methods are the operations of the API.

    Every method builds the operation's variables (typed and documented like the
    funcs plugin's functions) and hands them to a method of ``self``:

    ```python
    class BeastApi:
        def get_beasts(self) -> List[Beast]:
            return self.execute(GetBeastsQuery, {}).beasts

        async def aget_beasts(self) -> List[Beast]:
            return (await self.aexecute(GetBeastsQuery, {})).beasts

        def watch_beast(self, id: ID) -> Iterator[Beast]:
            for event in self.subscribe(WatchBeastSubscription, {"id": id}):
                yield event.watch_beast
    ```

    The class it is mixed into, or one of ``client_bases``, implements those four
    delegates; the generated module does not import an executor.
    """

    config: ClientPluginConfig

    def generate_ast(
        self,
        client_schema: GraphQLSchema,
        config: GeneratorConfig,
        registry: ClassRegistry,
    ) -> List[ast.AST]:
        # The global coercible maps are the defaults; this plugin's entries win.
        plugin_config = self.config.model_copy(
            update={
                "coercible_scalars": {
                    **config.coercible_scalars,
                    **self.config.coercible_scalars,
                },
                "coercible_inputs": {
                    **config.coercible_inputs,
                    **self.config.coercible_inputs,
                },
            }
        )

        documents = parse_documents(
            client_schema, plugin_config.documents or config.documents, config
        )
        operations = [
            node
            for node in documents.definitions
            if isinstance(node, OperationDefinitionNode)
        ]

        methods = []
        for operation in operations:
            # Awaitable first, as the funcs configs this replaces listed them.
            for is_async in (True, False):
                if is_async and not plugin_config.async_methods:
                    continue
                if not is_async and not plugin_config.sync_methods:
                    continue
                methods.append(
                    generate_method(
                        operation,
                        is_async,
                        client_schema,
                        config,
                        plugin_config,
                        registry,
                    )
                )

        return [generate_client_class(methods, plugin_config, registry)]
