---
sidebar_position: 5
sidebar_label: "Operations Funcs"
---

# Operations Funcs

This plugin generates functions for each operation in the schema.

Contrary to the `operations` plugin, this plugin generates real python function
with type annotations and docstrings according to the operation definition.

These functions the can be used to call a proxy function (specified through the config)
to execute the operation.

You can also specify a list of extra arguments and keyword arguments that will be passed to the proxy function.

Please consult the examples for some more explaination on how to use this plugin
'gql-usage' and 'rath-usage'

### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.operations.OperationsPlugin
            prepend_sync: ""
            prepend_async: "a"
            collapse_lonely: True #bool = True Collapses one operation query and return the collapsed type
            global_args: #List[Arg] = [] global additional arguments for the functions to be called
            global_kwargs: #List[Kwarg] = []
            definitions: #List[FunctionDefinition] = []
```

Definitions Sepcify a strategy to generate a proxy function

```yaml
definitions:
  type: # OperationType subscrpition, query, mutation
  is_async: #bool = False should we generate an async function
  extra_args: # List[Arg] = [] A list ofadditional arguments to be passed
  extra_kwargs: # List[Kwarg] = [] # A list of keyworad arguments to be passed
  use: path.to.the.function #the function we should proxy to signature def(document, variables, *extra_args, **extra_kwargs)
```

Args can be defined as such

```yaml
extra_args:
  key: #str
  type: #str
  description: #str = "Specify that in turms.plugin.funcs.OperationsFuncPlugin"
```

```yaml
extra_kwargs:
  key: #str
  type: #str
  description: #str = "Specify that in turms.plugin.funcs.OperationsFuncPlugin"
  default: #str = None
```

### Example Config
