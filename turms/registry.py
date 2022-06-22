import abc
import ast
from typing import List, Dict, Union, Iterable, Callable, Set
from turms.config import GeneratorConfig
from keyword import iskeyword
from turms.errors import (
    NoEnumFound,
    NoInputTypeFound,
    NoScalarFound,
    RegistryError,
)
from turms.stylers.base import Styler
from rich import get_console

SCALAR_DEFAULTS = {
    "ID": "str",
    "String": "str",
    "Int": "int",
    "Boolean": "bool",
    "GenericScalar": "typing.Dict",
    "DateTime": "str",
    "Float": "float",
}


graphql_built_in_enums_map = {
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
}


class BaseTypeRegistry(abc.ABC):
    def __init__(self, stylers: Iterable[Styler]):
        self.stylers: Iterable[Styler] = stylers
        self.type_map: Dict[str, str] = {}
        self.forward_references: Set[str] = set()

    @staticmethod
    @abc.abstractmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        raise NotImplementedError

    def style_type(self, typename: str):
        for styler in self.stylers:
            typename = self._get_styler_method(styler)(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_type(self, typename: str) -> str:
        assert (
            typename not in self.type_map
        ), "Type was already registered, cannot register again"
        classname = self.style_type(typename)
        self.type_map[typename] = classname
        return classname

    def get_type(self, typename: str) -> str:
        if typename not in self.type_map:
            raise RegistryError(f"Type {typename} not found. Needs to be registered first!")
        return self.type_map[typename]

    def generate_type_reference(
        self, typename: str, parent: str, allow_forward=True
    ) -> Union[ast.Name, ast.Constant]:
        classname = self.style_type(typename)
        if typename not in self.type_map or parent == classname:
            if not allow_forward:
                raise RegistryError(
                    f"Type {typename} is not yet defined but referenced by {parent}. "
                    f"And we dont allow forward references"
                )
            self.forward_references.add(parent)
            return ast.Constant(value=classname, ctx=ast.Load())
        return ast.Name(id=classname, ctx=ast.Load())


class InputTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_input_name


class EnumTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_enum_name


class ObjectTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_object_name


class InterfaceTypeRegistry(BaseTypeRegistry):
    def __init__(self, *args, **kwargs):
        super(InterfaceTypeRegistry, self).__init__(*args, **kwargs)
        self.interface_reference_map: Dict[str, str] = {}

    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_object_name

    def generate_type(self, typename: str) -> str:
        classname = self.style_type(typename)
        self.type_map[typename] = classname + "Base"
        self.interface_reference_map[typename] = classname
        return classname + "Base"

    def generate_type_reference(
        self, typename: str, parent: str, allow_forward=True
    ) -> Union[ast.Name, ast.Constant]:
        classname = self.style_type(typename)
        self.forward_references.add(parent)
        return ast.Constant(value=classname, ctx=ast.Load())


class FragmentTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_fragment_name


class QueryTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_query_name


class MutationTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_mutation_name


class SubscriptionTypeRegistry(BaseTypeRegistry):
    @staticmethod
    def _get_styler_method(styler: Styler) -> Callable[[str], str]:
        return styler.style_subscription_name


class ClassRegistry(object):
    def __init__(self, config: GeneratorConfig, stylers: List[Styler]):
        self.stylers = stylers
        self.config = config

        self._imports = set()
        self._builtins = set()
        self._builtins_forward_references = set()

        self._scalar_map = {**SCALAR_DEFAULTS, **config.scalar_definitions}
        self._fragment_document_map = {}

        self._input_type_registry = InputTypeRegistry(stylers)
        self._enum_type_registry = EnumTypeRegistry(stylers)
        self._object_type_registry = ObjectTypeRegistry(stylers)
        self._interface_type_registry = InterfaceTypeRegistry(stylers)

        self._fragment_type_registry = FragmentTypeRegistry(stylers)
        self._query_type_registry = QueryTypeRegistry(stylers)
        self._mutation_type_registry = MutationTypeRegistry(stylers)
        self._subscription_type_registry = SubscriptionTypeRegistry(stylers)

        self._console = get_console()

    @property
    def forward_references(self) -> Set[str]:
        return set.union(
            self._builtins_forward_references,
            self._input_type_registry.forward_references,
            self._enum_type_registry.forward_references,
            self._object_type_registry.forward_references,
            self._interface_type_registry.forward_references,
            self._fragment_type_registry.forward_references,
            self._query_type_registry.forward_references,
            self._mutation_type_registry.forward_references,
            self._subscription_type_registry.forward_references
        )

    def style_inputtype_class(self, typename: str):
        return self._input_type_registry.style_type(typename)

    def generate_inputtype(self, typename: str):
        return self._input_type_registry.generate_type(typename)

    def get_inputtype_class(self, typename) -> str:
        return self._input_type_registry.get_type(typename)

    def reference_inputtype(
            self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        try:
            return self._input_type_registry.generate_type_reference(
                typename, parent, allow_forward
            )
        except RegistryError:
            raise NoInputTypeFound(
                f"Input type {typename} is not yet defined but referenced by {parent}. "
                f"And we dont allow forward references"
            )

    def style_enum_class(self, typename: str):
        return self._enum_type_registry.style_type(typename)

    def generate_enum(self, typename: str):
        return self._enum_type_registry.generate_type(typename)

    def get_enum_class(self, typename) -> str:
        return self._enum_type_registry.get_type(typename)

    def reference_enum(
            self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        if self._is_builtin_enum(typename):
            return self._reference_builtin_enum(typename, parent)

        try:
            return self._enum_type_registry.generate_type_reference(
                typename, parent, allow_forward
            )
        except RegistryError:
            raise NoEnumFound(
                f"Enum type {typename} is not yet defined but referenced by {parent}. "
                f"And we dont allow forward references"
            )

    @staticmethod
    def _is_builtin_enum(typename: str) -> bool:
        return typename in graphql_built_in_enums_map

    def _reference_builtin_enum(self, typename: str, parent: str) -> ast.Constant:
        self._builtins.add(typename)
        self._builtins_forward_references.add(parent)
        return ast.Constant(value=typename, ctx=ast.Load())

    def style_objecttype_class(self, typename: str):
        return self._object_type_registry.style_type(typename)

    def generate_objecttype(self, typename: str):
        return self._object_type_registry.generate_type(typename)

    def reference_object(
        self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        return self._object_type_registry.generate_type_reference(
            typename, parent, allow_forward
        )

    def style_interface_class(self, typename: str):
        return self._interface_type_registry.style_type(typename)

    def generate_interface(self, typename: str):
        return self._interface_type_registry.generate_type(typename)

    def inherit_interface(self, typename: str) -> str:
        return self._interface_type_registry.get_type(typename)

    def reference_interface(
            self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        return self._interface_type_registry.generate_type_reference(
            typename, parent, allow_forward
        )

    def style_fragment_class(self, typename: str):
        return self._fragment_type_registry.style_type(typename)

    def generate_fragment(self, typename: str):
        return self._fragment_type_registry.generate_type(typename)

    def reference_fragment(
            self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        return self._fragment_type_registry.generate_type_reference(
            typename, parent, allow_forward
        )

    def inherit_fragment(self, typename: str) -> str:
        return self._fragment_type_registry.get_type(typename)

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
        return self._query_type_registry.style_type(typename)

    def generate_query(self, typename: str):
        return self._query_type_registry.generate_type(typename)

    def reference_query(
        self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        return self._query_type_registry.generate_type_reference(
            typename, parent, allow_forward
        )

    def style_mutation_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_mutation_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_mutation(self, typename: str):
        return self._mutation_type_registry.generate_type(typename)

    def reference_mutation(
        self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        return self._mutation_type_registry.generate_type_reference(
            typename, parent, allow_forward
        )

    def style_subscription_class(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_subscription_name(typename)
        if iskeyword(typename):
            typename += "_"
        return typename

    def generate_subscription(self, typename: str):
        return self._subscription_type_registry.generate_type(typename)

    def reference_subscription(
        self, typename: str, parent: str, allow_forward=True
    ) -> ast.AST:
        return self._subscription_type_registry.generate_type_reference(
            typename, parent, allow_forward
        )

    def register_import(self, name):
        if name in ("bool", "str", "int", "float", "dict", "list", "tuple"):
            return

        assert "." in name, "Please only register imports with a top level package"
        self._imports.add(name)

    def generate_imports(self):
        imports = []

        top_level = {}
        for name in self._imports:
            top_level.setdefault(".".join(name.split(".")[:-1]), set()).add(
                name.split(".")[-1]
            )

        for top_level_name, sub_level_names in top_level.items():
            imports.append(
                ast.ImportFrom(
                    module=top_level_name,
                    names=[ast.alias(name=name) for name in sub_level_names],
                    level=0,
                )
            )

        return imports

    def generate_builtins(self):
        return [graphql_built_in_enums_map[built_in] for built_in in self._builtins]

    def generate_forward_refs(self):
        tree = []

        for reference in sorted(self.forward_references):
            tree.append(
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(
                                id=reference,
                                ctx=ast.Load(),
                            ),
                            attr="update_forward_refs",
                            ctx=ast.Load(),
                        ),
                        keywords=[],
                        args=[],
                    )
                )
            )

        return tree

    def register_fragment_document(self, typename: str, cls: str):
        assert cls not in self._fragment_document_map, f"{cls} already registered"
        self._fragment_document_map[typename] = cls

    def get_fragment_document(self, typename: str):
        return self._fragment_document_map[typename]

    def reference_scalar(self, scalar_type: str):
        if scalar_type in self._scalar_map:
            python_type = self._scalar_map[scalar_type]
            if "." in python_type:
                # We make the assumption that the scalar type is a fully qualified class name
                self.register_import(python_type)

            return ast.Name(
                id=python_type.split(".")[-1], ctx=ast.Load()
            )  # That results only in the class name (also in the case of a builtin)

        raise NoScalarFound(
            f"No python equivalent found for {scalar_type}. Please define in scalar_definitions"
        )

    def warn(self, message):
        self._console.print("[r]" + message)
