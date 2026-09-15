"""A mapped ``@secured`` directive must actually be enforced.

The directive alone is metadata: strawberry prints it into the schema and never
acts on it. These tests cover the plugin turning it into a
``PermissionExtension``, so the rule is checked at resolve time while the printed
schema keeps advertising it.
"""

import importlib.util
import sys
import textwrap

import pytest
import strawberry
from graphql import parse
from strawberry.printer import print_schema

from turms.config import GeneratorConfig
from turms.errors import GenerationError
from turms.plugins.strawberry import StrawberryPlugin, StrawberryPluginConfig
from turms.run import build_ast_schema, generate_code

PERMISSIONS_MODULE = """
from strawberry.permission import BasePermission


class Base(BasePermission):
    message = "errors.unauthorizedAccess"
    error_extensions = {"errorType": "UNAUTHORIZED_ACCESS"}

    def has_permission(self, source, info, **kwargs):
        return self.allows(info.context or {}, kwargs)


class AdminOnly(Base):
    def allows(self, context, kwargs):
        return "ADMIN" in (context.get("roles") or [])


class Authenticated(Base):
    def allows(self, context, kwargs):
        return bool(context.get("auth"))


class AdminOrOwner(Base):
    def allows(self, context, kwargs):
        roles = context.get("roles") or []
        return "ADMIN" in roles or str(context.get("user_id")) == str(
            kwargs.get("id")
        )


admin_only = AdminOnly()
authenticated = Authenticated()
admin_or_owner = AdminOrOwner()
"""

ADMIN_REQUIRES = "@authService.hasRole(#authentication, 'ADMIN')"
AUTH_REQUIRES = "@authService.isAuthenticated(#authentication)"
OWNER_REQUIRES = "@authService.isAdminOrOwner(#authentication, #id)"

SCHEMA = """
directive @secured(requires: String!) on FIELD_DEFINITION

type Query {
    adminSecret: String @secured(requires: "%s")
    myProfile: String @secured(requires: "%s")
    user(id: ID!): String @secured(requires: "%s")
    publicInfo: String
}
""" % (ADMIN_REQUIRES, AUTH_REQUIRES, OWNER_REQUIRES)

MAPPING = {
    ADMIN_REQUIRES: "secureperm.admin_only",
    AUTH_REQUIRES: "secureperm.authenticated",
    OWNER_REQUIRES: "secureperm.admin_or_owner",
}


def _load(schema_src, mapping, tmp_path, **config_kwargs):
    """Generate the schema module, import it beside a permissions module."""
    plugin = StrawberryPlugin(
        config=StrawberryPluginConfig(secured_permissions=mapping, **config_kwargs)
    )

    code = generate_code(
        GeneratorConfig(skip_forwards=True),
        schema=build_ast_schema(parse(schema_src)),
        plugins=[plugin],
    )

    (tmp_path / "secureperm.py").write_text(textwrap.dedent(PERMISSIONS_MODULE))
    generated = tmp_path / "generated.py"
    generated.write_text(code)

    sys.path.insert(0, str(tmp_path))
    sys.modules.pop("secureperm", None)

    # strawberry resolves field origins through sys.modules, so the module has to
    # be registered under its own name before it is executed.
    name = f"generated_{abs(hash(code))}"
    spec = importlib.util.spec_from_file_location(name, generated)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("secureperm", None)

    return module, code


def test_mapped_directive_denies_and_allows(tmp_path):
    module, code = _load(SCHEMA, MAPPING, tmp_path)
    schema = strawberry.Schema(query=module.Query)

    assert "PermissionExtension(" in code
    assert "use_directives=False" in code

    denied = schema.execute_sync(
        "{ adminSecret }", context_value={"roles": ["EMPLOYEE"]}
    )
    assert denied.errors
    assert denied.errors[0].extensions == {"errorType": "UNAUTHORIZED_ACCESS"}

    allowed = schema.execute_sync("{ adminSecret }", context_value={"roles": ["ADMIN"]})
    assert allowed.errors is None


def test_authenticated_and_public_fields(tmp_path):
    module, _ = _load(SCHEMA, MAPPING, tmp_path)
    schema = strawberry.Schema(query=module.Query)

    assert schema.execute_sync("{ myProfile }", context_value={}).errors
    assert (
        schema.execute_sync("{ myProfile }", context_value={"auth": "u"}).errors is None
    )

    public = schema.execute_sync("{ publicInfo }", context_value={})
    assert public.errors is None


def test_field_arguments_reach_the_permission(tmp_path):
    """`isAdminOrOwner(#authentication, #id)` needs the resolved `id`."""
    module, _ = _load(SCHEMA, MAPPING, tmp_path)
    schema = strawberry.Schema(query=module.Query)

    owner = schema.execute_sync('{ user(id: "7") }', context_value={"user_id": "7"})
    assert owner.errors is None

    other = schema.execute_sync('{ user(id: "7") }', context_value={"user_id": "9"})
    assert other.errors
    assert other.errors[0].extensions == {"errorType": "UNAUTHORIZED_ACCESS"}

    admin = schema.execute_sync(
        '{ user(id: "7") }', context_value={"user_id": "9", "roles": ["ADMIN"]}
    )
    assert admin.errors is None


def test_printed_schema_keeps_the_directive(tmp_path):
    """Enforcement must not cost the wire contract with generated clients."""
    module, _ = _load(SCHEMA, MAPPING, tmp_path)
    sdl = print_schema(strawberry.Schema(query=module.Query))

    # one declaration plus the three secured fields, no duplicates
    assert sdl.count("@secured") == 4
    assert ADMIN_REQUIRES in sdl
    assert OWNER_REQUIRES in sdl


def test_unmapped_expression_fails_generation(tmp_path):
    """A rule nobody translated must break the build, not ship unprotected."""
    mapping = {k: v for k, v in MAPPING.items() if k != ADMIN_REQUIRES}

    with pytest.raises(GenerationError) as error:
        _load(SCHEMA, mapping, tmp_path)

    assert "no entry in `secured_permissions`" in str(error.value)


def test_unconfigured_plugin_is_unchanged(tmp_path):
    """Opt-in only: the defaults must not touch existing output."""
    module, code = _load(SCHEMA, {}, tmp_path)

    assert "PermissionExtension" not in code
    assert "strawberry.permission" not in code

    sdl = print_schema(strawberry.Schema(query=module.Query))
    assert sdl.count("@secured") == 4


INPUT_FIELD_SCHEMA = (
    """
directive @secured(requires: String!) on FIELD_DEFINITION | INPUT_FIELD_DEFINITION

input UserInput {
    roles: [String!]! @secured(requires: "%s")
}

type Query {
    q(i: UserInput!): String!
}
"""
    % ADMIN_REQUIRES
)


def test_input_field_directive_cannot_be_enforced(tmp_path):
    """An input field is never resolved, so the plugin must refuse rather than
    emit a declaration nothing checks."""
    with pytest.raises(GenerationError) as error:
        _load(INPUT_FIELD_SCHEMA, MAPPING, tmp_path)

    assert "INPUT_FIELD_DEFINITION" in str(error.value)


def test_input_field_directive_can_be_explicitly_accepted(tmp_path):
    _, code = _load(
        INPUT_FIELD_SCHEMA,
        MAPPING,
        tmp_path,
        secured_unenforced_locations=["INPUT_FIELD_DEFINITION"],
    )

    # accepted, so it stays a declaration and no permission is attached
    assert "PermissionExtension" not in code
