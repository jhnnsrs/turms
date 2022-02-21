---
sidebar_position: 1
sidebar_label: "Introduction"
---

# Quick Start

Let's discover **Turms in less than 5 minutes**.

### Inspiration

Turms is a graphql-codegen inspired code generator for pyhton that generates fully typed and
serialized operations from your graphql schema. Just define your query in standard graphql syntax
and let turms create fully typed queries/mutation and subscriptions, that you can use in your favourite
IDE.

### Installation

```bash
pip install turms
```

## Configuration

Turms relies on and complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction)

```yaml
projects:
  default:
    schema: http://api.spacex.land/graphql/
    documents: graphql/**.graphql
    extensions:
      turms: # path for configuration for turms
        out_dir: examples/api
        stylers:
          - type: turms.stylers.capitalize.Capitalizer
          - type: turms.stylers.snake.SnakeNodeName
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
          - type: turms.plugins.inputs.InputsPlugin
          - type: turms.plugins.fragments.FragmentsPlugin
          - type: turms.plugins.operation.OperationsPlugin
          - type: turms.plugins.funcs.OperationsFuncPlugin
        processors:
          - type: turms.processor.black.BlackProcessor
          - type: turms.processor.isort.IsortProcessor
        scalar_definitions:
          uuid: str
          timestamptz: str
          Date: str
```
