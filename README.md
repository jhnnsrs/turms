# turms

[![codecov](https://codecov.io/gh/jhnnsrs/turms/branch/master/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/jhnnsrs/turms)
[![PyPI version](https://badge.fury.io/py/turms.svg)](https://pypi.org/project/turms/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/turms/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/turms.svg)](https://pypi.python.org/pypi/turms/)
[![PyPI status](https://img.shields.io/pypi/status/turms.svg)](https://pypi.python.org/pypi/turms/)
[![PyPI download month](https://img.shields.io/pypi/dm/turms.svg)](https://pypi.python.org/pypi/turms/)

**turms** is a [`graphql-codegen`](https://www.graphql-code-generator.com/)-inspired code generator for Python. It reads your GraphQL schema and documents and generates fully typed, serializable Python code — Pydantic models for clients, Strawberry types for servers. Write your queries in plain GraphQL, and get autocomplete, type checking, and validation in your IDE for free.

```graphql
query get_countries($filter: CountryFilterInput) {
  countries(filter: $filter) {
    code
    name
  }
}
```

⬇️ `turms gen` ⬇️

```python
class GetCountriesCountries(BaseModel):
    typename: Optional[Literal["Country"]] = Field(alias="__typename")
    code: str
    name: str

class GetCountries(BaseModel):
    countries: List[GetCountriesCountries]

    class Arguments(BaseModel):
        filter: Optional[CountryFilterInput] = None

    class Meta:
        document = "query get_countries($filter: CountryFilterInput) { ... }"
```

turms is a **development-time tool only**: the generated code depends on Pydantic (or Strawberry), never on turms itself. Nothing of turms ships with your application.

## Features

- **Fully typed, fully documented** code generation — GraphQL descriptions become docstrings, deprecations become warnings
- **Client-side generation** from documents: enums, inputs, fragments and operations as Pydantic models (v2 and v1)
- **Server-side generation** from SDL schemas: typed [Strawberry](https://strawberry.rocks/) scaffolds with resolver stubs
- **Operation functions** — call `get_capsules()` instead of assembling query strings (sync and async, via the funcs plugin)
- **Transport agnostic** — works with [rath](https://github.com/jhnnsrs/rath), [gql](https://github.com/graphql-python/gql), or any HTTP client you like
- **Extensible pipeline** — plugins, parsers, stylers, and processors are all swappable and configurable
- **Custom scalars, custom bases, frozen (hashable) models, interface catch-alls**, and more
- **Code migration** — the merge processor preserves your hand-written resolver bodies across regenerations
- **[graphql-config](https://www.graphql-config.com/docs/user/user-introduction) compliant** — one config file, multiple projects
- **Watch mode** — regenerate on every save

## Installation

Because turms is a development-time tool that never becomes a runtime dependency, the easiest way to use it is to not install it at all and run it with [uvx](https://docs.astral.sh/uv/guides/tools/):

```bash
uvx turms init   # scaffold a config
uvx turms gen    # generate code
```

uvx downloads turms into a cached, isolated environment and runs it — your project stays clean. `turms init` adapts to your environment: it only scaffolds formatter processors (black, isort) into the config when those tools are actually installed, so the generated config always works out of the box.

For reproducible builds, pin the version: `uvx "turms==0.11.0" gen`.

### As a project dev dependency

If you prefer turms tracked in your project (so the whole team uses the same version), add it as a development dependency:

```bash
uv add --dev "turms[black,isort]"     # uv
pip install "turms[black,isort]"      # pip / requirements-dev.txt
```

and run it with `uv run turms gen` (or plain `turms gen` in an activated environment). Optional extras pull in the tools used by specific components:

| Extra | Enables |
| --- | --- |
| `black` | `BlackProcessor` |
| `isort` | `IsortProcessor` |
| `ruff` | `RuffProcessor` |
| `merge` | `MergeProcessor` (libcst) |

Python 3.10 or higher is required.

## Quickstart

**1. Scaffold a config** in your project root:

```bash
uvx turms init
```

This creates a `graphql.config.yaml`:

```yaml
projects:
  default:
    schema: https://countries.trevorblades.com/
    documents: graphql/**.graphql
    extensions:
      turms:
        out_dir: examples/api
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
          - type: turms.plugins.funcs.FuncsPlugin
        scalar_definitions:
          uuid: str
```

If formatters are installed in your environment, `init` also wires them up — e.g. with black and isort available, a `processors` section with `BlackProcessor` and `IsortProcessor` is added automatically.

**2. Write a query** in `graphql/countries.graphql`:

```graphql
fragment Continent on Continent {
  code
  name
}

query get_countries($filter: CountryFilterInput) {
  countries(filter: $filter) {
    code
    name
    continent {
      ...Continent
    }
  }
}
```

**3. Generate:**

```bash
uvx turms gen
```

**4. Use the typed models** with the client of your choice — every field is validated, aliased, and autocompleted:

```python
from examples.api.schema import GetCountries, CountryFilterInput, StringQueryOperatorInput

variables = GetCountries.Arguments(
    filter=CountryFilterInput(code=StringQueryOperatorInput(eq="DE"))
)
response = my_client.execute(GetCountries.Meta.document, variables.model_dump(by_alias=True, exclude_unset=True))
countries = GetCountries(**response["data"])

for country in countries.countries:
    print(country.continent.name)  # typed all the way down
```

## How it works

turms runs your schema and documents through a four-stage pipeline, each stage pluggable through the config:

```
GraphQL schema + documents
        │
   ┌────▼────┐   generate Python AST nodes
   │ Plugins │   (enums, inputs, fragments, operations, funcs, strawberry…)
   └────┬────┘
   ┌────▼────┐   transform the AST
   │ Parsers │   (e.g. polyfill typing imports for older Python)
   └────┬────┘
   ┌────▼────┐   style class/field names as they are generated
   │ Stylers │   (snake_case, capitalize, suffix appending…)
   └────┬────┘
   ┌────▼────┐   post-process the rendered source code
   │Processors│  (black, isort, ruff, merge, custom commands…)
   └────┬────┘
        ▼
   out_dir/schema.py
```

### Plugins

Plugins generate the actual code. Enable them per project; order matters (enums and inputs should come before fragments and operations).

| Plugin | Generates |
| --- | --- |
| `turms.plugins.enums.EnumsPlugin` | `Enum` classes from GraphQL enums |
| `turms.plugins.inputs.InputsPlugin` | Pydantic models for input types |
| `turms.plugins.objects.ObjectsPlugin` | Pydantic models for schema object types |
| `turms.plugins.fragments.FragmentsPlugin` | Pydantic models for GraphQL fragments |
| `turms.plugins.operations.OperationsPlugin` | One Pydantic model per query/mutation/subscription, with nested `Arguments` and `Meta` (the exact document) |
| `turms.plugins.funcs.FuncsPlugin` | Typed, documented call functions per operation (sync + async) that delegate to your client through configurable proxies |
| `turms.plugins.strawberry.StrawberryPlugin` | A Strawberry server schema with typed resolver stubs |

The funcs plugin turns operations into plain function calls. With an executor proxy configured (see [`examples/rath-usage`](examples/rath-usage)):

```python
async def aget_capsules(rath: Rath = None) -> List[GetCapsulesCountries]:
    """get_capsules

    Arguments:
        rath (rath.Rath, optional): The client we want to use (defaults to the currently active client)

    Returns:
        List[GetCapsulesCountries]"""
    return (await aexecute(GetCapsules, {}, rath=rath)).countries
```

### Stylers

Stylers normalize GraphQL naming to Python conventions — renamed fields automatically receive a Pydantic `alias`, so serialization stays wire-compatible.

| Styler | Effect |
| --- | --- |
| `turms.stylers.default.DefaultStyler` | Capitalized class names + snake_case fields (recommended) |
| `turms.stylers.capitalize.CapitalizeStyler` | Capitalizes the first letter of class names |
| `turms.stylers.snake_case.SnakeCaseStyler` | Converts camelCase fields/arguments to snake_case |
| `turms.stylers.appender.AppenderStyler` | Appends configurable suffixes (`Fragment`, `Query`, `Mutation`, …) to class names |

### Processors

Processors run over the rendered source before it is written to disk.

| Processor | Purpose |
| --- | --- |
| `turms.processors.black.BlackProcessor` | Format with [black](https://github.com/psf/black) |
| `turms.processors.isort.IsortProcessor` | Sort imports with [isort](https://github.com/PyCQA/isort) |
| `turms.processors.ruff.RuffProcessor` | Format (`format: true`) and/or autofix lints (`fix: true`) with [ruff](https://github.com/astral-sh/ruff) |
| `turms.processors.command.CommandProcessor` | Pipe the code through any command via stdin/stdout, e.g. `command: "uvx ruff format -"` |
| `turms.processors.merge.MergeProcessor` | Merge regenerated code into the existing file, keeping your hand-written function bodies |
| `turms.processors.disclaimer.DisclaimerProcessor` | Prepend a "this file is generated" disclaimer |

### Parsers

| Parser | Purpose |
| --- | --- |
| `turms.parsers.polyfill.PolyfillPlugin` | Rewrites typing constructs for an older target `python_version` |

## Configuration

turms complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction) and discovers `graphql.config.yaml|yml|json|toml` (or `.graphqlrc.*`) in the working directory. Everything turms-specific lives under `extensions.turms` of a project. The most important options:

| Option | Default | Meaning |
| --- | --- | --- |
| `out_dir` | `"api"` | Output directory |
| `generated_name` | `"schema.py"` | Output file name |
| `documents` | – | Glob of documents (overrides the project-level `documents`) |
| `scalar_definitions` | `{}` | Map of custom GraphQL scalars to Python types (`DateTime: datetime.datetime`) — required for every non-standard scalar |
| `object_bases` | `["pydantic.BaseModel"]` | Base class(es) for generated models |
| `interface_bases` | – | Separate base classes for interfaces |
| `additional_bases` | `{}` | Extra bases per GraphQL type name (great for mixin "traits") |
| `freeze` | disabled | Generate frozen (immutable, hashable) models; configurable per kind, with include/exclude lists |
| `options` | disabled | Set Pydantic model options (`extra`, `use_enum_values`, `validate_assignment`, …) per kind |
| `exclude_typenames` | `false` | Skip `__typename` literal fields |
| `always_resolve_interfaces` | `true` | Resolve interfaces to concrete implementation unions |
| `create_catchall` | `true` | Add a catch-all model for unknown interface implementations |
| `skip_forwards` | `false` | Skip generating forward-reference updates |
| `pydantic_version` | `"v2"` | Target Pydantic major version (`"v1"` or `"v2"`) |
| `omited_document_rules` | `[]` | GraphQL validation rules to skip for documents |
| `dump_schema` / `dump_configuration` | `false` | Also write the resolved schema / project config next to the output |

Every option can also be supplied through environment variables with the `TURMS_` prefix (e.g. `TURMS_OUT_DIR=generated`), courtesy of Pydantic settings.

A schema can be an introspection URL (optionally with headers), a local SDL file, or a list of either:

```yaml
schema:
  - https://api.example.org/graphql:
      headers:
        Authorization: Bearer ${TOKEN}
```

See the [documentation website](https://jhnnsrs.github.io/turms) for the full configuration reference, including all per-plugin options.

### Custom scalars

GraphQL only ships five builtin scalars (`String`, `Int`, `Float`, `Boolean`, `ID`) — everything else (`DateTime`, `JSON`, `UUID`, …) is schema-specific, and turms requires you to decide what each one becomes in Python via `scalar_definitions`:

```yaml
scalar_definitions:
  DateTime: datetime.datetime # ISO strings are parsed into real datetime objects
  UUID: uuid.UUID             # validated UUIDs instead of raw strings
  JSON: typing.Any            # pass through untouched
  Slug: myapp.scalars.Slug    # your own type with custom validation
```

The mapping is more than a type annotation: because the generated models are Pydantic models, the type you choose drives **parsing and validation**. Map `DateTime` to `str` and you get raw strings; map it to `datetime.datetime` and every response is parsed into timezone-aware datetime objects on arrival — and serialized back correctly when you send inputs. Any dotted path works, so you can point at your own types (anything Pydantic can validate, e.g. a `str` subclass with `__get_pydantic_core_schema__`, or an annotated type with constraints) to centralize invariants like "a `Slug` is always lowercase" right in the deserialization layer.

### Traits: extending generated models

Generated code shouldn't be edited — but it can be **extended**. `additional_bases` injects your own mixin classes ("traits") as base classes of every generated model for a given GraphQL type:

```yaml
additional_bases:
  Country:
    - myapp.traits.CountryTrait
```

```python
# myapp/traits.py
from pydantic import BaseModel, field_validator

class CountryTrait(BaseModel):
    @field_validator("code", check_fields=False)
    @classmethod
    def code_must_be_upper(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("country codes are uppercase")
        return v

    @property
    def flag_url(self) -> str:
        return f"https://flagcdn.com/{self.code.lower()}.svg"
```

Now every generated model that selects the `Country` type — top-level objects, fragments, and even the deeply nested classes inside operation results — inherits the trait:

```python
class GetCountriesCountries(CountryTrait, BaseModel):
    code: str
    name: str
```

This gives you, everywhere that type appears:

- **Validators** — enforce domain invariants (`field_validator`, `model_validator`) on data the moment it arrives from the API
- **Computed properties and methods** — `country.flag_url`, conversion helpers (`.to_numpy()`, `.as_tuple()`), business logic that travels with the data
- **`isinstance` checks** — `isinstance(obj, CountryTrait)` works across all generated variants of the type, however deeply nested the selection was

Traits are prepended to the base list, so their method resolution order beats the generated defaults.

## Server-side generation (Strawberry)

Point turms at an SDL file and use the Strawberry plugin to scaffold a typed server:

```yaml
projects:
  default:
    schema: beasts.graphql
    extensions:
      turms:
        out_dir: server
        skip_forwards: true
        stylers:
          - type: turms.stylers.default.DefaultStyler
        plugins:
          - type: turms.plugins.strawberry.StrawberryPlugin
        processors:
          - type: turms.processors.disclaimer.DisclaimerProcessor
          - type: turms.processors.black.BlackProcessor
          - type: turms.processors.merge.MergeProcessor
```

```python
@strawberry.type
class Query:
    @strawberry.field(description="get all the beasts on the server")
    def beasts(self) -> Optional[List[Optional[Beast]]]:
        """get all the beasts on the server"""
        return None  # fill in your resolver — MergeProcessor keeps it on regeneration
```

With the `MergeProcessor` enabled you can evolve the schema and regenerate freely: your resolver implementations survive.

## CLI

| Command | Description |
| --- | --- |
| `turms init` | Create a starter `graphql.config.yaml` in the current directory. `--template` picks a scaffold (see below), `--config` the file name |
| `turms gen [PROJECT]` | Generate all (or one named) project. `--config` selects a config file explicitly |
| `turms watch [PROJECT]` | Watch the documents glob and regenerate on save |
| `turms download` | Download a project's schema as SDL (`--out` suffix, `--dir` target directory) |

### Init templates

`turms init --template <name>` scaffolds sensible defaults for common setups:

| Template | Scaffolds |
| --- | --- |
| `documents` (default) | Pydantic models (enums, inputs, fragments, operations) from your documents |
| `rath` | `documents` plus typed call functions for the [rath](https://github.com/jhnnsrs/rath) client (async + sync) |
| `gql` | `documents` plus typed call functions for the [gql](https://github.com/graphql-python/gql) client |
| `strawberry` | A server-side [Strawberry](https://strawberry.rocks/) schema from a local SDL file, with disclaimer and merge-on-regenerate |

Every template adapts to your environment: formatter processors (black, isort — and merge for `strawberry`) are only included when the tools are actually installed.

## Examples

The [`examples/`](examples) directory contains complete, runnable setups:

| Example | Shows |
| --- | --- |
| [`pydantic-basic`](examples/pydantic-basic) | Plain document-based generation of Pydantic models |
| [`rath-usage`](examples/rath-usage) | Funcs plugin with async/sync proxies for the [rath](https://github.com/jhnnsrs/rath) client |
| [`gql-usage`](examples/gql-usage) | Funcs plugin with the [gql](https://github.com/graphql-python/gql) client passed as argument |
| [`beasts-strawberry`](examples/beasts-strawberry) | Server-side Strawberry schema generation with merge-on-regenerate |
| [`countries-code`](examples/countries-code) | Minimal generated client for the countries API |

## Transport layer

turms deliberately ships **no transport layer** — it generates models and (optionally) functions that delegate to whichever client you configure. If you want an Apollo-like GraphQL client for Python, have a look at [rath](https://github.com/jhnnsrs/rath), which pairs particularly well with turms.

## Development

turms uses [uv](https://github.com/astral-sh/uv) for project management:

```bash
uv sync --all-extras --dev   # install everything
uv run pytest                # run the test suite
uv run pytest --snapshot-update   # update generation snapshots after intentional changes
```

The architecture is plugin-first: to add your own plugin, subclass `turms.plugins.base.Plugin` and implement `generate_ast(client_schema, config, registry)`; to add a processor, subclass `turms.processors.base.Processor` and implement `run(gen_file, config)`. Any importable class can be referenced from the config by its dotted path — no registration step needed.

Contributions are welcome! Please open an issue or PR on [GitHub](https://github.com/jhnnsrs/turms).

## Why "turms"?

In Etruscan religion, Turms (usually written as 𐌕𐌖𐌓𐌌𐌑 *Turmś* in the Etruscan alphabet) was the equivalent of Roman Mercury and Greek Hermes — the **messenger** god between people and gods. turms is the messenger between your GraphQL schema and your Python code.

## License

MIT
