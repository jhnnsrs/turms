from turms.config import GeneratorConfig
from turms.plugins.enums import EnumsPlugin
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.run import generate_ast
from turms.stylers.default import DefaultStyler

from .utils import unit_test_with


def test_generation(mro_test_schema):
    config = GeneratorConfig()

    generated_ast = generate_ast(
        config,
        mro_test_schema,
        stylers=[DefaultStyler()],
        plugins=[
            EnumsPlugin(),
            InputsPlugin(),
            ObjectsPlugin(),
        ],
    )
    unit_test_with(generated_ast, "ThisWorks(foo='hallo', bar='good')")
