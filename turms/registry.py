import ast
from keyword import iskeyword
from typing import Callable, Dict, List, Set, Type

from graphql import DocumentNode, GraphQLNamedType

from turms.config import GeneratorConfig, LogFunction, PythonType
from turms.errors import (
    NoEnumFound,
    NoInputTypeFound,
    NoScalarFound,
    RegistryError,
)
from turms.stylers.base import Styler

SCALAR_DEFAULTS: Dict[str, str] = {
    "ID": "str",
    "String": "str",
    "Int": "int",
    "Boolean": "bool",
    "GenericScalar": "typing.Dict",
    "DateTime": "datetime.datetime",
    "Float": "float",
}

# Annotated metadata markers generated into the output module (unless the user
# overrides them via config). Authored as source and parsed to AST for clarity.
_GRAPHQL_DEFAULT_SRC = """
class GraphQLDefault:
    'Records a GraphQL field schema default value. The client omits the field so the server applies its own default; this preserves the value for introspection.'

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return 'GraphQLDefault(' + repr(self.value) + ')'
"""

_DEPRECATED_SRC = """
class Deprecated:
    'Marks a field as deprecated, carrying the GraphQL deprecation reason.'

    def __init__(self, reason=None):
        self.reason = reason

    def __repr__(self):
        return 'Deprecated(' + repr(self.reason) + ')'
"""


built_in_map = {
    "__TypeKind": ast.ClassDef(
        "__TypeKind",
        bases=[
            ast.Name(id="str", ctx=ast.Load()),
            ast.Name(id="Enum", ctx=ast.Load()),
        ],
        decorator_list=[],
        keywords=[],
        body=[
            ast.Assign(
                targets=[ast.Name(id=str(value), ctx=ast.Store())],
                value=ast.Constant(value=value),
            )
            for value in ["OBJECT", "INTERFACE", "UNION", "ENUM", "INPUT_OBJECT"]
        ],
    ),
    "__DirectiveLocation": ast.ClassDef(
        "__DirectiveLocation",
        bases=[
            ast.Name(id="str", ctx=ast.Load()),
            ast.Name(id="Enum", ctx=ast.Load()),
        ],
        decorator_list=[],
        keywords=[],
        body=[
            ast.Assign(
                targets=[ast.Name(id=str(value), ctx=ast.Store())],
                value=ast.Constant(value=value),
            )
            for value in [
                "SCALAR",
                "OBJECT",
                "FIELD_DEFINITION",
                "ARGUMENT_DEFINITION",
                "INTERFACE",
                "UNION",
                "ENUM",
                "ENUM_VALUE",
                "INPUT_OBJECT",
                "INPUT_FIELD_DEFINITION",
                "SCHEMA",
            ]
        ],
    ),
    "UNSET": [
        # Sentinel distinguishing "argument not provided" (omitted on serialize so
        # the server applies its default) from an explicitly passed ``None``.
        ast.ClassDef(
            "UnsetType",
            bases=[],
            decorator_list=[],
            keywords=[],
            body=[
                ast.Expr(
                    value=ast.Constant(
                        value=(
                            "Sentinel for arguments the caller did not provide. "
                            "Such fields are omitted on serialization so the GraphQL "
                            "server applies its own default."
                        )
                    )
                ),
                ast.Assign(
                    targets=[ast.Name(id="_instance", ctx=ast.Store())],
                    value=ast.Constant(value=None),
                ),
                ast.FunctionDef(
                    "__new__",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="cls")],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=[
                        ast.If(
                            test=ast.Compare(
                                left=ast.Attribute(
                                    value=ast.Name(id="cls", ctx=ast.Load()),
                                    attr="_instance",
                                    ctx=ast.Load(),
                                ),
                                ops=[ast.Is()],
                                comparators=[ast.Constant(value=None)],
                            ),
                            body=[
                                ast.Assign(
                                    targets=[
                                        ast.Attribute(
                                            value=ast.Name(id="cls", ctx=ast.Load()),
                                            attr="_instance",
                                            ctx=ast.Store(),
                                        )
                                    ],
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Call(
                                                func=ast.Name(id="super", ctx=ast.Load()),
                                                args=[],
                                                keywords=[],
                                            ),
                                            attr="__new__",
                                            ctx=ast.Load(),
                                        ),
                                        args=[ast.Name(id="cls", ctx=ast.Load())],
                                        keywords=[],
                                    ),
                                )
                            ],
                            orelse=[],
                        ),
                        ast.Return(
                            value=ast.Attribute(
                                value=ast.Name(id="cls", ctx=ast.Load()),
                                attr="_instance",
                                ctx=ast.Load(),
                            )
                        ),
                    ],
                    decorator_list=[],
                ),
                ast.FunctionDef(
                    "__repr__",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="self")],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=[ast.Return(value=ast.Constant(value="UNSET"))],
                    decorator_list=[],
                ),
                ast.FunctionDef(
                    "__bool__",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[ast.arg(arg="self")],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=[ast.Return(value=ast.Constant(value=False))],
                    decorator_list=[],
                ),
            ],
        ),
        ast.Assign(
            targets=[ast.Name(id="UNSET", ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="UnsetType", ctx=ast.Load()),
                args=[],
                keywords=[],
            ),
        ),
    ],
    "GraphQLDefault": ast.parse(_GRAPHQL_DEFAULT_SRC).body[0],
    "Deprecated": ast.parse(_DEPRECATED_SRC).body[0],
}  # builtin map provides the default types for any schema if they are referenced


class ClassRegistry(object):
    """Class Registry is responsible for keeping track of all the classes that are generated
    as well as their names. It also keeps track of all the imports that are required for the
    generated code to work, as well as all the forward references that are required
    for the generated code to work (i.e. when a class references another class that has not
    yet been defined). Class Registry provides a facade to the rest of the code to abstract
    the logic behind the stylers."""

    def __init__(
        self, config: GeneratorConfig, stylers: List[Styler], log: LogFunction
    ):
        self.stylers: List[Styler] = stylers
        self._imports: Set[str] = set()
        self._builtins: Set[str] = set()
        self.config: GeneratorConfig = config

        self.scalar_map: Dict[str, str] = {
            **SCALAR_DEFAULTS,
            **config.scalar_definitions,
        }
        # map of fragment typename to the strinigify graphql document
        self.fragment_document_map: Dict[str, str] = {}

        self.enum_class_map: Dict[str, str] = {}
        self.inputtype_class_map: Dict[str, str] = {}
        self.object_class_map: Dict[str, str] = {}
        self.interface_reference_map: Dict[str, str] = {}
        self.interface_baseclass_map: Dict[str, str] = {}

        self.operation_class_map: Dict[str, str] = {}
        self.fragment_class_map: Dict[str, str] = {}
        self.query_class_map: Dict[str, str] = {}
        self.subscription_class_map: Dict[str, str] = {}
        self.mutation_class_map: Dict[str, str] = {}

        self.registered_interfaces_fragments: Dict[str, ast.AST] = {}
        self.registered_union_fragments: Dict[str, str] = {}
        self.forward_references: Set[str] = set()
        self.fragment_type_map: Dict[str, GraphQLNamedType] = {}

        # Maps for the interface fragments and union fragments
        self.interfacefragments_impl_map: Dict[str, Dict[str, str]] = {}
        self.unionfragment_members_map: Dict[str, Dict[str, str]] = {}

        self.operation_single_operation_map: Dict[
            str, ast.AST
        ] = {}  # This is used to store the operation name and the root operation class name if single
        self.log = log

    def register_operation_single(self, operation_name: str, annotation_ast: ast.AST):
        self.operation_single_operation_map[operation_name] = annotation_ast

    def get_operation_single_or_none(self, operation_name: str):
        return (
            self.operation_single_operation_map[operation_name]
            if operation_name in self.operation_single_operation_map
            else None
        )

    def style_inputtype_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_input_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_inputtype(self, typename: str):
        assert typename not in self.inputtype_class_map, (
            "Type was already registered, cannot register annew"
        )
        classname = self.style_inputtype_class(typename)
        self.inputtype_class_map[typename] = classname
        return classname

    def get_inputtype_class(self, typename: str) -> str:
        return self.inputtype_class_map[typename]

    def reference_inputtype(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.Name | ast.Constant:
        classname = self.style_inputtype_class(typename)
        if typename not in self.inputtype_class_map or parent == classname:
            if not allow_forward:
                raise NoInputTypeFound(
                    f"Input type {typename} is not yet defined but referenced by {parent}. And we dont allow forward references"
                )
            self.forward_references.add(parent)
            return ast.Constant(value=classname)
        return ast.Name(id=self.inputtype_class_map[typename], ctx=ast.Load())

    def style_enum_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_enum_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_enum(self, typename: str):
        assert typename not in self.enum_class_map, (
            "Type was already registered, cannot register annew"
        )
        classname = self.style_enum_class(typename)
        self.enum_class_map[typename] = classname
        return classname

    def register_builtin(self, typename: str) -> None:
        """Register a builtin definition (from ``built_in_map``) to be emitted at
        the top of the generated module. Deduplicated via the builtins set."""
        self._builtins.add(typename)

    def get_enum_class(self, typename: str) -> str:
        return self.enum_class_map[typename]

    def reference_enum(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.Constant | ast.Name:
        if typename in built_in_map:
            # Builtin enums
            self._builtins.add(typename)
            self.forward_references.add(parent)
            return ast.Constant(value=typename)

        classname = self.style_enum_class(typename)
        if typename not in self.enum_class_map or parent == classname:
            if not allow_forward:
                raise NoEnumFound(
                    f"Input type {typename} is not yet defined but referenced by {parent}. And we dont allow forward references"
                )
            self.forward_references.add(parent)
            return ast.Constant(value=classname)
        return ast.Name(id=classname, ctx=ast.Load())

    def style_objecttype_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_object_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_objecttype(self, typename: str):
        assert typename not in self.object_class_map, (
            "Type was already registered, cannot register annew"
        )
        classname = self.style_objecttype_class(typename)
        self.object_class_map[typename] = classname
        return classname

    def reference_object(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.AST:
        return self._reference_generic(
            typename,
            parent,
            self.style_objecttype_class,
            self.object_class_map,
            "Object",
            allow_forward,
        )

    def _reference_generic(
        self,
        typename: str,
        parent: str,
        style_func: Callable[[str], str],
        class_map: Dict[str, str],
        error_class: str,
        allow_forward: bool = True,
    ) -> ast.Name | ast.Constant:
        classname = style_func(typename)
        if typename not in class_map or parent == classname:
            if not allow_forward:
                raise RegistryError(
                    f"""{error_class} type {typename} is not yet defined but referenced by {parent}. And we dont allow forward references"""
                )
            self.forward_references.add(parent)
            return ast.Constant(value=classname)
        return ast.Name(id=classname, ctx=ast.Load())

    def style_interface_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_object_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_interface(self, typename: str, with_base: bool = True):
        assert typename not in self.interface_baseclass_map, (
            "Type was already registered, cannot register annew"
        )
        classname = self.style_interface_class(typename)
        if with_base:
            self.interface_baseclass_map[typename] = classname + "Base"
        else:
            self.interface_baseclass_map[typename] = classname
        self.interface_reference_map[typename] = classname
        return self.interface_baseclass_map[typename]

    def inherit_interface(self, typename: str, allow_forward: bool = True) -> str:
        if typename not in self.interface_baseclass_map:
            raise RegistryError(
                f"Interface type {typename} is not yet defined but referenced. Please define it first."
            )
        return self.interface_baseclass_map[typename]

    def reference_interface(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.AST:
        # Interface need always be udpated later
        classname = self.style_interface_class(typename)
        self.forward_references.add(parent)
        return ast.Constant(value=classname)

    def style_fragment_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_fragment_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_fragment(self, fragmentname: str, is_interface: bool = False):
        assert fragmentname not in self.fragment_class_map, (
            f"Fragment {fragmentname} was already registered, cannot register annew"
        )
        classname = self.style_fragment_class(fragmentname)
        real_classname = classname if not is_interface else classname
        self.fragment_class_map[fragmentname] = real_classname
        return real_classname

    def register_fragment_type(self, fragmentname: str, typename: GraphQLNamedType):
        self.fragment_type_map[fragmentname] = typename

    def register_interface_fragment_implementations(
        self, fragmentname: str, implementationMap: Dict[str, str]
    ):
        self.interfacefragments_impl_map[fragmentname] = implementationMap

    def get_interface_fragment_implementations(self, fragmentname: str):
        return self.interfacefragments_impl_map[fragmentname]

    def register_union_fragment_members(
        self, fragmentname: str, membersMap: Dict[str, str]
    ):
        self.unionfragment_members_map[fragmentname] = membersMap

    def get_union_fragment_members(self, fragmentname: str):
        return self.unionfragment_members_map[fragmentname]

    def get_fragment_type(self, fragmentname: str):
        return self.fragment_type_map[fragmentname]

    def reference_fragment(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.Name | ast.Constant:
        return self._reference_generic(
            typename,
            parent,
            self.style_fragment_class,
            self.fragment_class_map,
            "Fragment",
            allow_forward,
        )

    def is_interface_fragment(self, typename: str):
        return typename in self.registered_interfaces_fragments

    def reference_interface_fragment(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.AST:
        return self.registered_interfaces_fragments[typename]

    def register_interface_fragment(self, typename: str, ast: ast.AST):
        self.registered_interfaces_fragments[typename] = ast

    def inherit_fragment(self, typename: str, allow_forward: bool = True) -> str:
        if typename not in self.fragment_class_map:
            raise RegistryError(
                f"Fragment {typename} is not yet defined but referenced by. Please change the order in your fragments."
            )
        return self.fragment_class_map[typename]

    def generate_node_name(self, node_name: str):
        for styler in self.stylers:
            node_name = styler.style_node_name(node_name)

        if iskeyword(node_name):
            return node_name + "_"

        return node_name

    def generate_parameter_name(self, node_name: str):
        for styler in self.stylers:
            node_name = styler.style_parameter_name(node_name)

        if iskeyword(node_name):
            return node_name + "_"

        return node_name

    def style_query_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_query_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_query(self, typename: str):
        assert typename not in self.query_class_map, (
            f"Type {typename} was already registered, cannot register annew"
        )
        classname = self.style_query_class(typename)
        self.query_class_map[typename] = classname
        return classname

    def reference_query(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.AST:
        return self._reference_generic(
            typename,
            parent,
            self.style_query_class,
            self.query_class_map,
            "Query",
            allow_forward,
        )

    def style_mutation_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_mutation_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_mutation(self, typename: str):
        assert typename not in self.mutation_class_map, (
            f"Type {typename} was already registered, cannot register annew"
        )
        classname = self.style_mutation_class(typename)
        self.mutation_class_map[typename] = classname
        return classname

    def reference_mutation(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.AST:
        return self._reference_generic(
            typename,
            parent,
            self.style_mutation_class,
            self.mutation_class_map,
            "Mutation",
            allow_forward,
        )

    def style_subscription_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_subscription_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_subscription(self, typename: str):
        assert typename not in self.subscription_class_map, (
            f"Type {typename} was already registered, cannot register annew"
        )
        classname = self.style_subscription_class(typename)
        self.subscription_class_map[typename] = classname
        return classname

    def reference_subscription(
        self, typename: str, parent: str, allow_forward: bool = True
    ) -> ast.AST:
        return self._reference_generic(
            typename,
            parent,
            self.style_subscription_class,
            self.subscription_class_map,
            "Subscription",
            allow_forward,
        )

    def register_import(self, name: str) -> None:
        if name in ("bool", "str", "int", "float", "dict", "list", "tuple"):
            return

        self._imports.add(name)

    def generate_imports(self) -> List[ast.AST]:
        """Generate the imports for the generated code. This is used to generate the"""
        imports: List[ast.AST] = []

        lone_top_imports: Set[str] = set()
        top_level: Dict[str, Set[str]] = {}
        for name in self._imports:
            if "." not in name:
                lone_top_imports.add(name)
            else:
                top_level.setdefault(".".join(name.split(".")[:-1]), set()).add(
                    name.split(".")[-1]
                )

        for lone_top_import in lone_top_imports:
            imports.append(ast.Import(names=[ast.alias(name=lone_top_import)]))

        for top_level_name, sub_level_names in top_level.items():
            imports.append(
                ast.ImportFrom(
                    module=top_level_name,
                    names=[ast.alias(name=name) for name in sub_level_names],
                    level=0,
                )
            )

        return imports

    def generate_builtins(self) -> List[ast.AST]:
        """Generate the builtins for the generated code. This is used to generate the"""
        builtins: list[ast.AST] = []

        for built_in in self._builtins:
            node = built_in_map[built_in]
            if isinstance(node, list):
                builtins.extend(node)
            else:
                builtins.append(node)

        return builtins

    def generate_forward_refs(self) -> List[ast.AST]:
        tree: list[ast.AST] = []

        for reference in sorted(self.forward_references):
            tree.append(
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(
                                id=reference,
                                ctx=ast.Load(),
                            ),
                            attr=(
                                "model_rebuild"
                                if self.config.pydantic_version == "v2"
                                else "update_forward_refs"
                            ),
                            ctx=ast.Load(),
                        ),
                        keywords=[],
                        args=[],
                    )
                )
            )

        return tree

    def register_fragment_document(self, typename: str, document: str) -> None:
        assert typename not in self.fragment_document_map, (
            f"{typename} already registered"
        )
        self.fragment_document_map[typename] = document

    def get_fragment_document(self, typename: str) -> str:
        return self.fragment_document_map[typename]

    def reference_unset(self) -> ast.Name:
        """Returns the name of the UNSET sentinel instance, importing the user's
        override (config.unset_instance) or generating the builtin bundle."""
        override = self.config.unset_instance
        if override:
            self.register_import(override)
            return ast.Name(id=override.split(".")[-1], ctx=ast.Load())
        self.register_builtin("UNSET")
        return ast.Name(id="UNSET", ctx=ast.Load())

    def reference_unset_type(self) -> ast.Name:
        """Returns the name of the UNSET sentinel type, importing the user's
        override (config.unset_type_class) or generating the builtin bundle."""
        override = self.config.unset_type_class
        if override:
            self.register_import(override)
            return ast.Name(id=override.split(".")[-1], ctx=ast.Load())
        self.register_builtin("UNSET")
        return ast.Name(id="UnsetType", ctx=ast.Load())

    def reference_graphql_default(self) -> ast.Name:
        """Returns the name of the GraphQLDefault metadata marker, importing the
        user's override (config.graphql_default_class) or generating the builtin."""
        override = self.config.graphql_default_class
        if override:
            self.register_import(override)
            return ast.Name(id=override.split(".")[-1], ctx=ast.Load())
        self.register_builtin("GraphQLDefault")
        return ast.Name(id="GraphQLDefault", ctx=ast.Load())

    def reference_deprecated(self) -> ast.Name:
        """Returns the name of the Deprecated metadata marker, importing the user's
        override (config.deprecated_class) or generating the builtin."""
        override = self.config.deprecated_class
        if override:
            self.register_import(override)
            return ast.Name(id=override.split(".")[-1], ctx=ast.Load())
        self.register_builtin("Deprecated")
        return ast.Name(id="Deprecated", ctx=ast.Load())

    def register_scalar(self, scalar_type: str, python_type: str):
        self.scalar_map[scalar_type] = python_type

    def reference_scalar(self, scalar_type: str):
        if scalar_type in self.scalar_map:
            python_type = self.scalar_map[scalar_type]
            if "." in python_type:
                # We make the assumption that the scalar type is a fully qualified class name
                self.register_import(python_type)

            return ast.Name(
                id=python_type.split(".")[-1], ctx=ast.Load()
            )  # That results only in the class name (also in the case of a builtin)

        raise NoScalarFound(
            f"No python equivalent found for {scalar_type}. Please define in scalar_definitions"
        )

    def warn(self, message: str) -> None:
        self.log(message, level="WARN")
