"""End-to-end tests for spec-compliant ``@oneOf`` input support.

A ``@oneOf`` input whose fields are distinct input object types (the tagged
input-union pattern) is generated as a direct ``Union`` of the member models
with a ``WrapSerializer`` restoring the ``{fieldName: memberDict}`` wire form
(pydantic v2 only). All other ``@oneOf`` inputs — scalar fields, duplicated
member types, or pydantic v1 — fall back to a union of per-field wrapper
classes whose single required field serializes to the tagged wire form through
the ordinary ``dict(by_alias=True, exclude_unset=True)`` proxy contract.
"""

import pytest
from graphql import parse

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.funcs import FuncsPlugin, FuncsPluginConfig, FunctionDefinition
from turms.plugins.inputs import InputsPlugin
from turms.plugins.objects import ObjectsPlugin
from turms.plugins.operations import OperationsPlugin
from turms.plugins.strawberry import StrawberryPlugin
from turms.run import build_ast_schema, generate_ast
from turms.stylers.default import DefaultStyler

from .utils import build_relative_glob, parse_to_code, unit_test_with


def _generate(oneof_schema, with_funcs=False):
    config = GeneratorConfig(
        documents=build_relative_glob("/documents/oneof/*.graphql"),
    )
    plugins = [InputsPlugin(), ObjectsPlugin(), OperationsPlugin()]
    if with_funcs:
        plugins.append(
            FuncsPlugin(
                config=FuncsPluginConfig(
                    definitions=[
                        FunctionDefinition(
                            type="query", use="mocks.query", is_async=False
                        )
                    ]
                )
            )
        )
    return generate_ast(
        config, oneof_schema, stylers=[DefaultStyler()], plugins=plugins
    )


def test_scalar_oneof_generates_wrapper_union(oneof_schema):
    """A @oneOf input with scalar fields becomes per-field wrapper classes whose
    single required field serializes to the tagged wire form (incl. aliases)."""
    generated_ast = _generate(oneof_schema)

    unit_test_with(
        generated_ast,
        """
        wire = FindUserInputEmail(email='x@y.z').dict(by_alias=True, exclude_unset=True)
        assert wire == {'email': 'x@y.z'}, wire

        aliased = SearchFilterAuthorId(authorId='42').dict(by_alias=True, exclude_unset=True)
        assert aliased == {'authorId': '42'}, aliased

        try:
            FindUserInputEmail()
        except Exception:
            pass
        else:
            raise AssertionError('missing required oneOf field must fail validation')

        args = FindUser.Arguments(input=FindUserInputEmail(email='x')).dict(
            by_alias=True, exclude_unset=True
        )
        assert args == {'input': {'email': 'x'}}, args
        """,
    )


def test_tagged_union_oneof_generates_direct_union(oneof_schema):
    """A @oneOf input whose fields are distinct input types becomes a direct
    union of the member models; the serializer restores the tag wrapping."""
    generated_ast = _generate(oneof_schema)

    unit_test_with(
        generated_ast,
        """
        args = FindPet.Arguments(pet=CatInput(name='whiskers')).dict(
            by_alias=True, exclude_unset=True
        )
        assert args == {'pet': {'cat': {'name': 'whiskers'}}}, args

        args = FindPet.Arguments(pet=DogInput(name='rex', bark=True)).dict(
            by_alias=True, exclude_unset=True
        )
        assert args == {'pet': {'dog': {'name': 'rex', 'bark': True}}}, args

        # Direct mode: the members ARE the union, no wrapper classes.
        assert 'PetInputCat' not in globals()
        assert '_serialize_pet_input' in globals()
        """,
    )


def test_duplicate_member_types_fall_back_to_wrappers():
    """When two fields share the same member type the tag cannot be recovered
    from the value's type, so wrapper classes are generated instead."""
    sdl = """
    directive @oneOf on INPUT_OBJECT

    input UserFilter {
      name: String
    }

    input Search @oneOf {
      byOwner: UserFilter
      byAuthor: UserFilter
    }

    type Query {
      search(input: Search!): String
    }
    """
    generated_ast = generate_ast(
        GeneratorConfig(),
        build_ast_schema(parse(sdl)),
        stylers=[DefaultStyler()],
        plugins=[InputsPlugin()],
    )

    unit_test_with(
        generated_ast,
        """
        wire = SearchByOwner(byOwner=UserFilter(name='x')).dict(
            by_alias=True, exclude_unset=True
        )
        assert wire == {'byOwner': {'name': 'x'}}, wire
        assert '_serialize_search' not in globals()
        """,
    )


def test_oneof_field_must_be_nullable():
    sdl = """
    directive @oneOf on INPUT_OBJECT

    input Bad @oneOf {
      a: String!
    }

    type Query {
      q(input: Bad!): String
    }
    """
    with pytest.raises(GenerationError, match="to be nullable"):
        generate_ast(
            GeneratorConfig(),
            build_ast_schema(parse(sdl)),
            stylers=[DefaultStyler()],
            plugins=[InputsPlugin()],
        )


def test_oneof_field_must_not_have_default():
    sdl = """
    directive @oneOf on INPUT_OBJECT

    input Bad @oneOf {
      a: String = "x"
    }

    type Query {
      q(input: Bad!): String
    }
    """
    with pytest.raises(GenerationError, match="default"):
        generate_ast(
            GeneratorConfig(),
            build_ast_schema(parse(sdl)),
            stylers=[DefaultStyler()],
            plugins=[InputsPlugin()],
        )


def test_full_stack_with_funcs(oneof_schema):
    """The whole Operations + Funcs stack generates importable code over oneOf
    documents (exercises registry references and forward refs)."""
    generated_ast = _generate(oneof_schema, with_funcs=True)
    unit_test_with(generated_ast, "")


def test_strawberry_emits_one_of_keyword(oneof_schema):
    """The strawberry plugin detects @oneOf via the SDL ast node (graphql-core
    3.2 has no is_one_of attribute) and emits strawberry.input(one_of=True)."""
    code = parse_to_code(
        generate_ast(
            GeneratorConfig(),
            oneof_schema,
            stylers=[DefaultStyler()],
            plugins=[StrawberryPlugin()],
        )
    )
    assert "one_of=True" in code
