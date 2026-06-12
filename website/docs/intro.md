---
sidebar_position: 1
sidebar_label: "Introduction"
---

# Quick Start

Let's discover **Turms in less than 5 minutes**.

### Goal

Turms is a `graphql-codegen` inspired code generator for python that generates typed and serializable python code from your graphql schema and documents. Just define your query in standard graphql syntax and let turms create fully typed queries/mutation and subscriptions, that you can use in your favourite IDE.

Turms allows you to easily generate both server-side and client-side code for your GraphQL API.

### Installation

Turms is a pure development-time tool: the generated code never depends on turms itself. The
recommended way to run it is therefore [uvx](https://docs.astral.sh/uv/guides/tools/), which
needs no installation at all:

```bash
uvx turms init
uvx turms gen
```

`turms init` adapts the scaffolded config to your environment: formatter processors (black,
isort) are only included when those tools are actually installed, so the generated config
works out of the box. Use `--template` to pick a different starter — `documents` (default,
pydantic models from your operations), `rath` or `gql` (documents plus typed call functions
for that client), or `strawberry` (server-side schema from a local SDL file).

Alternatively, add turms as a development dependency so your whole team uses the same pinned
version:

```bash
uv add --dev turms      # uv
pip install turms       # pip
```

:::tip
Turms requires python 3.10 or higher (as we rely on ast unparsing).
:::

### Configuration

Turms relies on and complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction) and searches your current working dir for the graphql-config file.

```yaml
projects:
  default:
    schema: https://countries.trevorblades.com/
    documents: graphql/**.graphql
    extensions:
      turms: # path for configuration for turms
        out_dir: api
        plugins: # path for plugin configuration
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operations.OperationsPlugin
          - type: turms.plugins.funcs.FuncsPlugin
        scalar_definitions:
          uuid: str
          timestamptz: str
          Date: str
```

:::tip
Each plugin has its own scope of configuration — see the [Config](config) reference for all
options.
:::

## Generation

```bash
uvx turms gen
```

Will generate python code according to the schema and your documents.
