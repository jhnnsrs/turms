from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, unit_test_with


def test_inline_fragment_on_object_type(complex_defaults_schema):
    """``... on X`` inside a selection already narrowed to X used to hard-fail.

    recurse.py raised ``NotImplementedError("Inline Fragments are not yet
    implemented")``, even though the construct is legal GraphQL and is the usual
    way to hang a @skip/@include on a group of fields. The parent type is
    already concrete, so the right treatment is to flatten.
    """
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/inline_on_object/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        complex_defaults_schema,
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            FragmentsPlugin(),
            OperationsPlugin(),
        ],
    )

    unit_test_with(
        generated_ast,
        # the unconditional group is flattened in as a normal field
        "s = InlineOnObjectSwatches.model_validate("
        "{'__typename': 'Swatch', 'color': 'RED', 'name': 'crimson'})\n"
        "assert s.color == Color.RED\n"
        "assert s.name == 'crimson'\n"
        # the spread inside the inline fragment became a base class
        "assert issubclass(InlineOnObjectSwatches, SwatchName)\n",
    )
