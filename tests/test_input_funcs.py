"""Tests for the input_funcs plugin: factory functions per input type."""

from graphql import build_ast_schema, parse

from turms.config import GeneratorConfig
from turms.plugins.input_funcs import InputFuncsPlugin, InputFuncsPluginConfig
from turms.plugins.inputs import InputsPlugin, InputsPluginConfig
from turms.run import generate_ast
from turms.stylers.snake_case import SnakeCaseStyler
from turms.stylers.capitalize import CapitalizeStyler

from .utils import parse_to_code, unit_test_with

schema_sdl = """
input AddressInput {
    street: String!
    zip: String
}

input UserInput {
    name: String!
    age: Int
    address: AddressInput
    tags: [String!]
}

type Query {
    hello(user: UserInput): String
}
"""


def _generate(**inputfuncs_kwargs):
    config = GeneratorConfig()
    return generate_ast(
        config,
        build_ast_schema(parse(schema_sdl)),
        stylers=[CapitalizeStyler(), SnakeCaseStyler()],
        plugins=[
            # skip_unreferenced off so the inputs are generated without documents
            InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False)),
            InputFuncsPlugin(
                config=InputFuncsPluginConfig(
                    skip_unreferenced=False, **inputfuncs_kwargs
                )
            ),
        ],
    )


def test_factory_signature_and_body():
    generated = parse_to_code(_generate())

    # Required field -> positional; optional fields -> Union[..., UnsetType] = UNSET.
    assert (
        "def user_input(name: str, age: Union[Optional[int], UnsetType]=UNSET, address: Union[Optional[AddressInput], UnsetType]=UNSET, tags: Union[Optional[Iterable[str]], UnsetType]=UNSET) -> UserInput:"
        in generated
    )
    # Body builds the dict conditionally and constructs the model.
    assert "data: Dict[str, Any] = {}" in generated
    assert "data['name'] = name" in generated
    assert "if age is not UNSET:" in generated
    assert "data['age'] = age" in generated
    assert "return UserInput(**data)" in generated
    # Nested input factory also generated.
    assert "def address_input(street: str" in generated
    assert "return AddressInput(**data)" in generated


def test_coercible_scalars_change_annotation():
    generated = parse_to_code(_generate(coercible_scalars={"String": "pathlib.Path"}))
    # The String params become coercible to Path, and Path is imported.
    assert "name: Path" in generated
    assert "from pathlib import Path" in generated


def test_global_coercible_scalars_are_used():
    """coercible_scalars set on the global GeneratorConfig apply without a per-plugin
    override."""
    config = GeneratorConfig(coercible_scalars={"String": "pathlib.Path"})
    generated = parse_to_code(
        generate_ast(
            config,
            build_ast_schema(parse(schema_sdl)),
            stylers=[CapitalizeStyler(), SnakeCaseStyler()],
            plugins=[
                InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False)),
                InputFuncsPlugin(
                    config=InputFuncsPluginConfig(skip_unreferenced=False)
                ),
            ],
        )
    )
    assert "name: Path" in generated
    assert "from pathlib import Path" in generated


def test_plugin_coercible_overrides_global():
    """A plugin's coercible_scalars entry overrides the global one for that scalar."""
    config = GeneratorConfig(coercible_scalars={"String": "pathlib.Path"})
    generated = parse_to_code(
        generate_ast(
            config,
            build_ast_schema(parse(schema_sdl)),
            stylers=[CapitalizeStyler(), SnakeCaseStyler()],
            plugins=[
                InputsPlugin(config=InputsPluginConfig(skip_unreferenced=False)),
                InputFuncsPlugin(
                    config=InputFuncsPluginConfig(
                        skip_unreferenced=False,
                        coercible_scalars={"String": "uuid.UUID"},
                    )
                ),
            ],
        )
    )
    # plugin override wins for String.
    assert "name: UUID" in generated
    assert "name: Path" not in generated


def test_prepend_function_name():
    generated = parse_to_code(_generate(prepend="make_"))
    assert "def make_user_input(" in generated
    assert "def make_address_input(" in generated


def test_runtime_construction():
    """The generated factories build valid models at runtime."""
    generated_ast = _generate()
    unit_test_with(
        generated_ast,
        """
        # only required field -> optional fields omitted (default None on model)
        u = user_input(name='alice')
        assert u.name == 'alice'
        assert u.age is None
        assert u.address is None

        # providing optionals + a nested input built via its own factory
        addr = address_input(street='Main', zip='12345')
        u2 = user_input(name='bob', age=30, address=addr, tags=['x', 'y'])
        assert u2.age == 30
        assert u2.address.street == 'Main'
        assert u2.tags == ['x', 'y']
        """,
    )


def test_unset_optionals_not_in_dump():
    """Omitted optionals are unset, so exclude_unset drops them (server defaults)."""
    generated_ast = _generate()
    unit_test_with(
        generated_ast,
        """
        u = user_input(name='alice')
        dumped = u.dict(by_alias=True, exclude_unset=True)
        assert dumped == {'name': 'alice'}, dumped
        """,
    )
