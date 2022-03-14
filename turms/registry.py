import ast
from distutils.command.config import config
from typing import List
from turms.config import GeneratorConfig
from keyword import iskeyword
from turms.errors import NoScalarEquivalentFound
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


class ClassRegistry(object):
    def __init__(self, config: GeneratorConfig, stylers: List[Styler]):
        self.stylers = stylers
        self._imports = set()
        self.config = config
        self.fragment_document_map = {}
        self.enum_class_map = {}
        self.inputtype_class_map = {}
        self.fragment_class_map = {}
        self.console = get_console()

    def generate_type_name_field(self, typename):
        return ast.AnnAssign(
            target=ast.Name(id="typename", ctx=ast.Store()),
            annotation=ast.Subscript(
                value=ast.Name(id="Optional", ctx=ast.Load()),
                slice=ast.Name("str", ctx=ast.Load()),
            ),
            value=ast.Call(
                func=ast.Name(id="Field", ctx=ast.Load()),
                args=[],
                keywords=[
                    ast.keyword(arg="alias", value=ast.Constant(value="__typename"))
                ],
            ),
            simple=1,
        )

    def generate_inputtype_classname(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_input_name(typename)

        if iskeyword(typename):
            return typename + "_"

        return typename

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

    def generate_fragment_classname(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_fragment_name(typename)

        if iskeyword(typename):
            return typename + "_"

        return typename

    def generate_enum_classname(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_enum_name(typename)

        if iskeyword(typename):
            return typename + "_"

        return typename

    def generate_query_classname(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_query_name(typename)

        if iskeyword(typename):
            return typename + "_"

        return typename

    def generate_mutation_classname(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_mutation_name(typename)

        if iskeyword(typename):
            return typename + "_"

        return typename

    def generate_subscription_classname(self, typename: str):
        for styler in self.stylers:
            typename = styler.style_subscription_name(typename)

        if iskeyword(typename):
            return typename + "_"

        return typename

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

    def register_enum_class(self, typename: str, cls: str):
        assert cls not in self.enum_class_map, f"{cls} already registered"
        self.enum_class_map[typename] = cls

    def register_inputtype_class(self, typename: str, cls: str):
        assert cls not in self.inputtype_class_map, f"{cls} already registered"
        self.inputtype_class_map[typename] = cls

    def register_fragment_class(self, typename: str, cls: str):
        assert cls not in self.fragment_class_map, f"{cls} already registered"
        self.fragment_class_map[typename] = cls

    def register_fragment_document(self, typename: str, cls: str):
        assert cls not in self.fragment_document_map, f"{cls} already registered"
        self.fragment_document_map[typename] = cls

    def get_inputtype_class(self, typename: str, allow_forward=True):
        try:
            return self.inputtype_class_map[typename]
        except KeyError as e:
            if allow_forward:
                return self.generate_inputtype_classname(typename)
            raise e

    def get_fragment_class(self, typename: str, allow_forward=True):
        try:
            return self.fragment_class_map[typename]
        except KeyError as e:
            if allow_forward:
                return self.generate_fragment_classname(typename)
            raise e

    def get_fragment_document(self, typename: str):
        return self.fragment_document_map[typename]

    def get_enum_class(self, typename: str, allow_forward=True):
        try:
            return self.enum_class_map[typename]
        except KeyError as e:
            if allow_forward:
                return self.generate_enum_classname(typename)
            raise e

    def get_scalar_equivalent(self, scalar_type: str):

        updated_dict = {**SCALAR_DEFAULTS, **self.config.scalar_definitions}

        try:
            scalar_type = updated_dict[scalar_type]
            if "." in scalar_type:
                # We make the assumption that the scalar type is a fully qualified class name
                self.register_import(scalar_type)
        except KeyError as e:
            raise NoScalarEquivalentFound(
                f"No python equivalent found for {scalar_type}. Please define in scalar_definitions"
            )

        return scalar_type.split(".")[-1]

    def warn(self, message):
        self.console.print("[r]" + message)
