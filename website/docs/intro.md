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

```bash
pip install turms
```

turms is a pure development library and will not introduce any dependency on itself into your
code, so we recommend installing turms as a development dependency.

```bash
poetry add -D turms

```

:::tip
As of now turms only supports python 3.9 and higher (as we rely on ast unparsing)
:::

### Configuration

Turms relies on and complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction) and searches your current working dir for the graphql-config file.

```yaml
projects:
  default:
    schema: http://api.spacex.land/graphql/
    documents: graphql/**.graphql
    extensions:
      turms: # path for configuration for turms
        out_dir: examples/api
        plugins: # path for plugin configuration
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operation.OperationsPlugin
          - type: turms.plugins.funcs.FuncsPlugin
        processors:
          - type: turms.processor.black.BlackProcessor
          - type: turms.processor.isort.IsortProcessor
        scalar_definitions:
          uuid: str
          timestamptz: str
          Date: str
```

:::tip
Each plugin as its own scope of configuration, that you can consult
::::

## Generation

```bash
turms gen
```

Will generate python code according to the schema and your documents.

