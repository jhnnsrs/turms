# turms — Copilot Instructions

## Project overview

**turms** is a `graphql-codegen`-inspired Python code generator that produces typed, serializable Pydantic models and operation functions from GraphQL schemas and documents. It supports both client-side (operations/fragments) and server-side (Strawberry schema types) generation.

- **Python**: 3.10+ required (`ast.unparse()` dependency)
- **Core dependencies**: `graphql-core`, `pydantic v2`, `pydantic-settings`, `rich-click`
- **Package manager**: `uv` (dev), `poetry` (build/publish)

## Build & test commands

```bash
uv run pytest                        # run all tests
uv run pytest tests/test_funcs.py    # run a single test file
uv run pytest --cov --cov-report xml:cov.xml  # with coverage
turms gen                            # generate code from graphql.config.yaml
turms watch                          # watch and regenerate on changes
turms init                           # scaffold a default graphql.config.yaml
```

Tests use **pytest-snapshot** for regression testing (snapshots in `snapshots/`). Fixtures are session-scoped and defined in `tests/conftest.py`. Schema files live in `tests/schemas/`.

## Architecture

Code generation is a pipeline with four stages:

```
Schema/Documents
      │
      ▼
  Plugins  → generate ast.AST nodes from GraphQL types/operations
      │
      ▼
  Parsers  → transform the collected AST list (e.g., polyfill compatibility)
      │
      ▼
  Stylers  → rename identifiers (snake_case, capitalize, append suffix, etc.)
      │
      ▼
Processors → post-process the rendered source string (black, isort, merge)
      │
      ▼
  Output file
```

The **`ClassRegistry`** (`turms/registry.py`) is threaded through the entire pipeline, storing generated types so plugins can reference each other's output without duplication.  
The **`ReferenceRegistry`** (`turms/referencer.py`) enables `skip_unreferenced`: it walks operation/fragment ASTs recursively to determine which schema types are actually needed.

### Key directories

| Path | Role |
|---|---|
| `turms/plugins/` | AST generators per GraphQL construct (enums, inputs, fragments, operations, funcs, objects, strawberry) |
| `turms/processors/` | Source-string transformers: `black`, `isort`, `merge` (libcst), `disclaimer` |
| `turms/stylers/` | Identifier transformers: `default`, `snake_case`, `capitalize`, `appender` |
| `turms/parsers/` | AST-level post-processors (currently: `polyfill`) |
| `turms/config.py` | All Pydantic config models (`GeneratorConfig`, `GraphQLProject`, etc.) |
| `turms/registry.py` | `ClassRegistry` — resolves types across plugins |
| `turms/referencer.py` | `ReferenceRegistry` — determines which types are reachable |
| `turms/run.py` | Orchestration: loads schema, runs pipeline, writes files |
| `turms/cli/` | `rich-click` CLI commands (`gen`, `watch`, `download`, `init`) |
| `tests/schemas/` | GraphQL SDL fixture schemas |
| `tests/documents/` | GraphQL document fixtures (queries, mutations, fragments) |
| `snapshots/` | Snapshot files for pytest-snapshot regression tests |

## Plugin authoring conventions

Every plugin:
- Subclasses `Plugin` from `turms/plugins/base.py`
- Implements `generate_ast(client_schema, config, registry) → Sequence[ast.AST]`
- Has an inner `PluginConfig(BaseSettings)` with `extra="forbid"`
- Registers generated types in `ClassRegistry` for cross-plugin resolution

**Plugin ordering matters**: plugins run sequentially. `EnumsPlugin` must precede `OperationsPlugin`; `InputsPlugin` must precede `FragmentsPlugin` if inputs appear in fragment variables.

## Configuration conventions

Projects are configured in `graphql.config.yaml` under `extensions.turms`:

```yaml
projects:
  default:
    schema: https://example.com/graphql  # URL, file glob, or SDL string
    documents: graphql/**.graphql
    extensions:
      turms:
        out_dir: api/
        scalar_definitions:           # GraphQL scalar → Python type
          uuid: str
          DateTime: "datetime.datetime"
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
        processors:
          - type: turms.processors.black.BlackProcessor
          - type: turms.processors.isort.IsortProcessor
        options:
          freeze:
            enabled: true             # generate immutable/hashable models
```

- Configs use **Pydantic v2** throughout (`ConfigDict`, `field_validator`, `model_validator`). Extra fields are **forbidden** on all config models — be precise.
- Scalars not listed in `scalar_definitions` raise `NoScalarFound` at generation time.

## Common pitfalls

- **Plugin order**: missing enum/input plugin before operations → `NoEnumFound` / `NoInputFound` error.
- **Custom scalars**: every non-standard scalar (UUID, DateTime, JSON…) must be mapped in `scalar_definitions`.
- **CWD at runtime**: `turms gen` scans the **current working directory** for `graphql.config.yaml`. Run from the project root.
- **AST unparsing**: all generation works on Python `ast` objects; string manipulation of generated code bypasses the pipeline — always extend via plugins or processors.
- **Merge processor**: uses libcst for semantic merging. Do not attempt line-based string merging of generated files.
- **Snapshot tests**: update snapshots with `uv run pytest --snapshot-update` when intentional output changes are made.
- **Pydantic v2**: use `model_rebuild()` for forward references; avoid v1 patterns (`__fields__`, `validator`, `orm_mode`).

## Testing guidance

- Add new tests in `tests/` mirroring the existing file-per-feature pattern.
- Test helpers live in `tests/utils.py` (e.g., `build_relative_glob()`).
- Fixture schemas go in `tests/schemas/`, documents in `tests/documents/`.
- Use `@pytest.mark.parametrize` for variant configs where appropriate.
- Snapshot tests for output regression: call `assert result == snapshot` and commit the snapshot file.
