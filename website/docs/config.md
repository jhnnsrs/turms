---
sidebar_position: 5
sidebar_label: "Config"
---

# Config

Turms relies on and complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction) and searches
your current working dir for the graphql-config file. It currently supports the following formats:

- graphql.config.yaml / .graphqlrc.yaml
- graphql.config.yml / .graphqlrc.yml
- graphql.config.toml / .graphqlrc.toml
- graphql.config.json / .graphqlrc.json

A typical configuration looks like this:

```yaml
projects:
  default:
    schema: https://countries.trevorblades.com/
    documents: graphql/**.graphql
    extensions:
      turms: # configuration for turms
        out_dir: api
        stylers:
          - type: turms.stylers.default.DefaultStyler
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
        processors:
          - type: turms.processors.black.BlackProcessor
          - type: turms.processors.isort.IsortProcessor
        scalar_definitions:
          uuid: str
          timestamptz: str
          Date: str
```

We recommend the `projects` layout to ensure support for multiple graphql projects, but a single
project configuration (the project keys at top level) is also supported.

## Schema sources

The `schema` key accepts:

- **An introspection URL**: `schema: https://countries.trevorblades.com/`
- **An introspection URL with headers**:
  ```yaml
  schema:
    https://api.example.org/graphql:
      headers:
        Authorization: Bearer xxxx
  ```
- **A local SDL file or glob**: `schema: schema/*.graphql`
- **A list** of any of the above (schemas get merged)

## The turms section

Everything turms-specific lives under `extensions.turms` of a project. Configuration is
validated by pydantic — unknown keys are rejected, so typos fail loudly.

### General options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `out_dir` | `str` | `"api"` | The output directory for the generated file |
| `generated_name` | `str` | `"schema.py"` | The name of the generated file within `out_dir` |
| `documents` | `str` | – | Glob of documents to parse; overrides the project-level `documents` |
| `domain` | `str` | – | Domain of the GraphQL API (set as a config variable) |
| `verbose` | `bool` | `false` | Enable verbose logging |
| `exit_on_error` | `bool` | `true` | Exit with code 1 if a project fails to generate |
| `allow_introspection` | `bool` | `true` | Allow introspection queries when fetching remote schemas |
| `dump_schema` | `bool` | `false` | Also write the resolved schema into `out_dir` |
| `schema_name` | `str` | `"schema.graphql"` | File name used by `dump_schema` |
| `dump_configuration` | `bool` | `false` | Also write the resolved project configuration into `out_dir` |
| `configuration_name` | `str` | `"project.json"` | File name used by `dump_configuration` |

### Code generation options

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `pydantic_version` | `"v1"` \| `"v2"` | `"v2"` | Which pydantic major version the generated code targets |
| `object_bases` | `List[str]` | `["pydantic.BaseModel"]` | Base class(es) for generated models |
| `interface_bases` | `List[str]` | – | Separate base classes for interfaces (defaults to `object_bases`) |
| `always_resolve_interfaces` | `bool` | `true` | Resolve interfaces to unions of concrete types |
| `create_catchall` | `bool` | `true` | Add a catch-all type for interface implementations unknown to the local schema |
| `exclude_typenames` | `bool` | `false` | Do not generate `__typename` literal fields |
| `skip_forwards` | `bool` | `false` | Skip generating forward-reference updates (`model_rebuild`) |
| `scalar_definitions` | `Dict[str, str]` | `{}` | Map of GraphQL scalar → python type (builtin or dotted import path) |
| `coercible_scalars` | `Dict[str, str]` | `{}` | Global map of scalar → a coercible python type used in generated function/factory params. Plugins (`funcs`, `input_funcs`) merge their own on top |
| `graphql_default_class` | `str` | – | Dotted path to your own class used as the `GraphQLDefault` Annotated marker. If unset, one is generated into the module |
| `deprecated_class` | `str` | – | Dotted path to your own class used as the `Deprecated` Annotated marker. If unset, one is generated into the module |
| `document_field_metadata` | `bool` | `true` | Fold the GraphQL deprecation reason and default value into the field documentation, in addition to the Annotated markers |
| `unset_type_class` | `str` | – | Dotted path to your own UNSET sentinel **type**. If unset, one is generated. Must be set with `unset_instance` |
| `unset_instance` | `str` | – | Dotted path to your own UNSET sentinel **instance**. If unset, one is generated. Must be set with `unset_type_class` |
| `additional_bases` | `Dict[str, List[str]]` | `{}` | Extra base classes per GraphQL type name (dotted import paths) |
| `additional_config` | `Dict[str, Dict]` | `{}` | Extra pydantic config attributes per GraphQL type name |
| `force_plugin_order` | `bool` | `true` | Run plugins strictly in their configured order |
| `omited_document_rules` | `List[str]` | `[]` | GraphQL document validation rules to skip |

### Scalar definitions

Every scalar in your schema that is not a GraphQL builtin (`String`, `Int`, `Float`, `Boolean`, `ID`)
**must** be mapped to a python type, otherwise generation fails with `NoScalarFound`:

```yaml
scalar_definitions:
  uuid: str
  DateTime: datetime.datetime
  JSON: typing.Any
  Slug: myapp.scalars.Slug
```

Builtin names (`str`, `int`, ...) are used directly; anything containing a dot is imported.

The mapping is more than a type annotation: because the generated models are pydantic models, the
type you choose drives **parsing and validation**. Map `DateTime` to `str` and you get raw strings;
map it to `datetime.datetime` and every response is parsed into real datetime objects on arrival —
and serialized back correctly when you send inputs. Useful patterns:

- **Stdlib types with parsing**: `datetime.datetime`, `datetime.date`, `uuid.UUID`,
  `decimal.Decimal`, `pathlib.Path` — pydantic validates and converts the wire format for you.
- **Pass-through**: `typing.Any` for free-form scalars like `JSON`.
- **Your own types**: point at any type pydantic can validate (e.g. a `str` subclass implementing
  `__get_pydantic_core_schema__`) to centralize invariants like "a `Slug` is always lowercase"
  right in the deserialization layer.

### Default values & the UNSET model

GraphQL **schema defaults are not baked into the generated client**. A field with
a default (`Int! = 5`, `Int = 10`) is emitted as **optional, defaulting to
`None`**, and the value is owned by the server. The convenience functions
default optional parameters to an `UNSET` sentinel and only send the ones the
caller provided — combined with `exclude_unset=True` serialization in your
executor proxy, omitted arguments are absent from the wire so the server applies
its own defaults.

The original default and any deprecation reason are preserved as introspectable
`Annotated` markers (`GraphQLDefault`, `Deprecated`). The relevant options are
`graphql_default_class`, `deprecated_class`, `document_field_metadata`,
`unset_type_class`, and `unset_instance` (see the table above).

:::warning Breaking change
If you are upgrading from a version that baked defaults, your executor proxy must
now serialize with `exclude_unset=True`. See the
[Defaults & UNSET migration guide](migration-defaults-unset) for the full
walkthrough.
:::

### Traits (`additional_bases`)

Generated code shouldn't be edited — but it can be extended. `additional_bases` injects your own
mixin classes as base classes of every generated model for a given GraphQL type — object types,
fragments, and the nested classes inside operation results alike:

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

Use traits to add **validators**, **computed properties and methods**, and to enable
**`isinstance` checks** across all generated variants of a type. Traits are prepended to the base
list, so their method resolution order beats the generated defaults. See
[Traits](design/traits) for details.

### Freezing models (`freeze`)

Generate faux-immutable, hashable models — handy for caching and use as dict keys:

```yaml
freeze:
  enabled: true
  types: [input, fragment, object] # which kinds to freeze (default)
  exclude: [BigDataFragment] # type names to skip
  include: [] # or explicitly include
  convert_list_to_tuple: true # GraphQL lists become tuples (hashable)
```

| Option | Default | Description |
| --- | --- | --- |
| `enabled` | `false` | Enable freezing |
| `types` | `[input, fragment, object]` | Which GraphQL kinds to freeze |
| `include` / `exclude` | – | Explicit type-name allow/deny lists |
| `include_fields` / `exclude_fields` | `[]` | Field-level allow/deny lists |
| `convert_list_to_tuple` | `true` | Convert `List[...]` annotations to `Tuple[..., ...]` |

### Pydantic options (`options`)

Set pydantic model configuration on the generated classes, per GraphQL kind:

```yaml
options:
  enabled: true
  extra: forbid # ignore | allow | forbid
  use_enum_values: true
  validate_assignment: true
  allow_population_by_field_name: true
  types: [input, fragment, object]
```

`include` / `exclude` lists by type name are supported here as well. `allow_mutation` and `orm_mode`
are available for pydantic v1 targets.

## Component sections

Each of the four pipeline stages is configured as a list of importable classes. Every entry needs a
`type` (the dotted python path of the class); all remaining keys are passed to that component's own
config:

```yaml
extensions:
  turms:
    plugins:
      - type: turms.plugins.enums.EnumsPlugin
        skip_underscore: true # plugin-specific option
      - type: turms.plugins.fragments.FragmentsPlugin
        fragment_bases:
          - pydantic.BaseModel
    stylers:
      - type: turms.stylers.default.DefaultStyler
    parsers:
      - type: turms.parsers.polyfill.PolyfillPlugin
        python_version: "3.9"
    processors:
      - type: turms.processors.ruff.RuffProcessor
        fix: true
```

Because components are resolved by import path, **your own classes work the same way** — point
`type` at any importable subclass of `Plugin`, `Styler`, `Parser`, or `Processor`.

### Plugins

| Plugin | Key options (default) |
| --- | --- |
| `turms.plugins.enums.EnumsPlugin` | `skip_underscore` (false), `skip_double_underscore` (true), `skip_unreferenced` (true), `prepend`/`append` ("") |
| `turms.plugins.inputs.InputsPlugin` | `inputtype_bases` (["pydantic.BaseModel"]), `allow_population_by_field_name` (true), `skip_underscore` (true), `skip_unreferenced` (true) |
| `turms.plugins.objects.ObjectsPlugin` | `types_bases` (["pydantic.BaseModel"]), `skip_underscore` (false), `skip_double_underscore` (true) |
| `turms.plugins.fragments.FragmentsPlugin` | `fragment_bases` ([]), `fragments_glob`, `add_documentation` (true), `generate_meta_class` (true) |
| `turms.plugins.operations.OperationsPlugin` | `query_bases`/`mutation_bases`/`subscription_bases` ([]), `operations_glob`, `create_arguments` (true), `extract_documentation` (true), `arguments_allow_population_by_field_name` (false) |
| `turms.plugins.funcs.FuncsPlugin` | `definitions` ([]), `global_args`/`global_kwargs` ([]), `prepend_sync` (""), `prepend_async` ("a"), `collapse_lonely` (true), `expand_input_types` ([]), `argument_key_is_styled` (false), `coercible_scalars` (\{\}) |
| `turms.plugins.input_funcs.InputFuncsPlugin` | `coercible_scalars` (\{\}), `skip_underscore` (true), `skip_unreferenced` (true), `prepend` (""), `extract_documentation` (true) — see [Input Funcs](plugins/inputfuncs) |
| `turms.plugins.strawberry.StrawberryPlugin` | `generate_directives` (true), `generate_scalars` (true), `builtin_directives`, `builtin_scalars` |

The funcs plugin's `definitions` describe how each operation type is turned into a function:

```yaml
- type: turms.plugins.funcs.FuncsPlugin
  global_kwargs:
    - type: rath.Rath
      key: rath
      description: "The client to use"
  definitions:
    - type: query # query | mutation | subscription
      is_async: true
      use: your_library.proxies.aexecute # the executor proxy to call
    - type: query
      is_async: false
      use: your_library.proxies.execute
```

### Stylers

| Styler | Effect |
| --- | --- |
| `turms.stylers.default.DefaultStyler` | Capitalized class names + snake_case fields (recommended) |
| `turms.stylers.capitalize.CapitalizeStyler` | Capitalizes the first letter of class names |
| `turms.stylers.snake_case.SnakeCaseStyler` | camelCase → snake_case for fields and arguments (adds pydantic aliases) |
| `turms.stylers.appender.AppenderStyler` | Appends suffixes per kind: `append_fragment` ("Fragment"), `append_query` ("Query"), `append_mutation` ("Mutation"), `append_subscription` ("Subscription"), `append_enum`/`append_input` ("") |

### Parsers

| Parser | Key options (default) |
| --- | --- |
| `turms.parsers.polyfill.PolyfillPlugin` | `python_version` ("3.9") — rewrites typing constructs for older python targets |

### Processors

| Processor | Key options (default) |
| --- | --- |
| `turms.processors.black.BlackProcessor` | – (requires `pip install black`) |
| `turms.processors.isort.IsortProcessor` | – (requires `pip install isort`) |
| `turms.processors.ruff.RuffProcessor` | `format` (true), `fix` (false) (requires `pip install ruff`) |
| `turms.processors.command.CommandProcessor` | `command` — pipe the code through any stdin/stdout command, e.g. `"uvx ruff format -"` |
| `turms.processors.merge.MergeProcessor` | Merges regenerated code with the existing file, keeping hand-written bodies (requires `pip install libcst`) |
| `turms.processors.disclaimer.DisclaimerProcessor` | `disclaimer` — text prepended to the generated file |

## Environment variables

All turms settings are pydantic settings and can be supplied via environment variables with the
`TURMS_` prefix, e.g.:

```bash
TURMS_OUT_DIR=generated TURMS_VERBOSE=1 turms gen
```

## CLI

| Command | Description |
| --- | --- |
| `turms init` | Create a starter `graphql.config.yaml`. `--template documents\|rath\|gql\|strawberry` picks the scaffold (default: `documents`), `--config` the file name |
| `turms gen [PROJECT]` | Generate all projects, or only the named one. `--config path` selects a config file |
| `turms watch [PROJECT]` | Watch the documents glob and regenerate on change |
| `turms download` | Download each project's schema as SDL. `--out` sets the file suffix, `--dir` the directory |

Note that `turms gen` must run from the directory containing the config file (or use `--config`),
and relative paths (documents, `out_dir`) resolve from the current working directory.
