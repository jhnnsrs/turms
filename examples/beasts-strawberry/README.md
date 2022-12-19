# Turms and Strawberry Usage

This example illustrates how you can use the python library `strawberry-graphql`
with turms and its schema generation plugin.

## Install

This example uses poetry to manage dependencies. You can install it
by running the following command:

```bash
poetry install
```

otherwise you can install strawberry by running:

```bash
pip install strawberry-graphql[debug-server]
```

:::note

Please note that turms (and libcst) is only a development dependency, the code only
requires strawberry-graphql to work

:::

# Test generation

This examples includes a graphql config file that utilizes the strawpberry plugin to generate strawberry types for you.

Importantly this example also include the (experimental) `MergeProcessor` which allows you to keepvchanges in the generated code. Simple alter your schema and turms will only regenerate
typing annotations and fields that map to the schema, every implementation in your resolver
functions should remain intact.

```yaml
projects:
  default:
    schema: beasts.graphql
    extensions:
      turms:
        skip_forwards: true
        out_dir: api
        stylers:
          - type: turms.stylers.capitalize.CapitalizeStyler
          - type: turms.stylers.snake_case.SnakeCaseStyler
        plugins:
          - type: turms.plugins.strawberry.StrawberryPlugin # generates a strawberry schema
        processors:
          - type: turms.processors.disclaimer.DisclaimerProcessor
          - type: turms.processors.black.BlackProcessor
          - type: turms.processors.isort.IsortProcessor
          - type: turms.processors.merge.MergeProcessor # merges the formated schema with already defined functions
        scalar_definitions:
          uuid: str
          _Any: typing.Any
```

### How to run code generation

```
turms gen
```
