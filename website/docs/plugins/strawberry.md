---
sidebar_position: 5
sidebar_label: "Operations Funcs"
---

# Strawberry

This plugin generates a fully fledged strawberry schema from your
SDL schema.

It is best used in combination with the MergeProcessor to enable only
updating type definitions and not overwriting added functionatly (like
resolvers)


### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.strawberry.StrawberryPlugin
            prepend_sync: ""
            prepend_async: "a"
            collapse_lonely: True #bool = True Collapses one operation query and return the collapsed type
            global_args: #List[Arg] = [] global additional arguments for the functions to be called
            global_kwargs: #List[Kwarg] = []
            definitions: #List[FunctionDefinition] = []
```

Definitions Sepcify a strategy to generate a proxy function



### Example Config
