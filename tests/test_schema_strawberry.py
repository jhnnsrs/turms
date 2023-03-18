
from turms.config import GeneratorConfig
from turms.run import generate_ast
from turms.plugins.strawberry import StrawberryPlugin, StrawberryPluginConfig
from turms.stylers.default import DefaultStyler
from turms.run import generate_ast
from .utils import unit_test_with


def test_countries_schema(countries_schema):
    config = GeneratorConfig(scalar_definitions={"_Any": "typing.Any"})

    generated_ast = generate_ast(
        config,
        countries_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_union_schema(union_schema):
    config = GeneratorConfig(scalar_definitions={"_Any": "typing.Any"})

    generated_ast = generate_ast(
        config,
        union_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_arkitekt_schema(arkitekt_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        arkitekt_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_multiple_interface(multi_interface_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        multi_interface_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_schema_directive_generation(schema_directive_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        schema_directive_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_custom_scalar_generation(scalar_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        scalar_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")


def test_custom_func_generation(scalar_schema):
    config = GeneratorConfig(
        scalar_definitions={
            "QString": "str",
            "Any": "str",
            "UUID": "pydantic.UUID4",
            "Callback": "str",
        }
    )

    generated_ast = generate_ast(
        config,
        scalar_schema,
        stylers=[DefaultStyler()],
        plugins=[
            StrawberryPlugin(
                config=StrawberryPluginConfig(
                    generate_directives_func="turms.plugins.strawberry.default_generate_directives",
                    skip_underscore=True,
                )
            ),
        ],
        skip_forwards=True,
    )

    unit_test_with(generated_ast, "")
