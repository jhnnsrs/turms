from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.fragments import FragmentsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.run import generate_ast
from turms.stylers.capitalize import CapitalizeStyler
from turms.stylers.snake_case import SnakeCaseStyler

from .utils import build_relative_glob, unit_test_with


def test_fragment_spread_inside_inline_fragment(multi_interface_schema):
    """A fragment spread inside an inline fragment must reach the model.

    It used to be dropped by a bare ``if not isinstance(field, FieldNode):
    continue``, so the generated class carried neither the spread's fields nor
    the fragment as a base -- while ``Meta.document`` still asked the server for
    them. The data came back and pydantic silently discarded it.
    """
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/spread_in_inline/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        multi_interface_schema,
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
        "node = FlowWithSpreadInInlineFlowNodesBaseArkitektNode.model_validate(\n"
        "    {'__typename': 'ArkitektNode', 'id': '1', 'name': 'n',\n"
        "     'package': 'pkg', 'kind': 'generator'}\n"
        ")\n"
        "assert node.package == 'pkg', 'spread field missing from the model'\n"
        "assert node.kind == 'generator', 'spread field missing from the model'\n"
        "assert node.name == 'n'\n"
        "assert isinstance(node, ArkitektExtras), 'spread should become a base class'\n",
    )


def test_directive_on_inline_fragment_makes_its_fields_optional(
    multi_interface_schema,
):
    """A @skip/@include on the inline fragment applies to every field inside it.

    ``kind`` is ``String!``, but the whole group is conditional, so it has to be
    generated as Optional. The directive check was originally wired only into
    the concrete-object branch; interface and union selections went through
    separate call sites that never received it.
    """
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/spread_in_inline/*.graphql"),
    )
    generated_ast = generate_ast(
        config,
        multi_interface_schema,
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
        "cls = ConditionalInlineFragmentFlowNodesBaseArkitektNode\n"
        "assert not cls.model_fields['kind'].is_required(),"
        " 'a conditional inline fragment must not produce required fields'\n"
        "m = cls.model_validate({'__typename': 'ArkitektNode', 'id': '1'})\n"
        "assert m.kind is None\n",
    )
