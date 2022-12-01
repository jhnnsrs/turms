---
sidebar_label: funcs
title: plugins.funcs
---

#### get\_definitions\_for\_onode

```python
def get_definitions_for_onode(operation_definition: OperationDefinitionNode,
                              plugin_config: FuncsPluginConfig) -> List[Arg]
```

Checks the Plugin Config if the operation definition should be included
in the generated functions

**Arguments**:

- `operation_definition` _OperationDefinitionNode_ - _description_
- `plugin_config` _FuncsPluginConfig_ - _description_
  

**Returns**:

- `List[Arg]` - _description_

#### get\_operation\_class\_name

```python
def get_operation_class_name(o: OperationDefinitionNode,
                             registry: ClassRegistry) -> str
```

Generates the name of the Operation Class for the given OperationDefinitionNode



**Arguments**:

- `o` _OperationDefinitionNode_ - The graphql o node
- `registry` _ClassRegistry_ - The registry (used to get the operation class name)
  

**Raises**:

- `Exception` - If the operation type is not supported
  

**Returns**:

- `str` - _description_

#### get\_return\_type\_annotation

```python
def get_return_type_annotation(o: OperationDefinitionNode,
                               client_schema: GraphQLSchema,
                               registry: ClassRegistry,
                               collapse: bool = True) -> ast.AST
```

Gets the return type annotation for the given operation definition node

Ulized an autocollapse feature to collapse the return type annotation if it is a single fragment,
to not generate unnecessary classes

## FuncsPlugin Objects

```python
class FuncsPlugin(Plugin)
```

This plugin generates functions for each operation in the schema.

Contratry to the `operations` plugin, this plugin generates real python function
with type annotations and docstrings according to the operation definition.

These functions the can be used to call a proxy function (specified through the config)
to execute the operation.

You can also specify a list of extra arguments and keyword arguments that will be passed to the proxy function.

Please consult the examples for more information.

**Example**:

  
```python

async def aexecute(operation: Model, variables: Dict[str, Any], client = None):
    client = client # is the grahql client that can be passed as an extra argument (or retrieved from a contextvar)
    x = await client.aquery(
        operation.Meta.document, operation.Arguments(**variables).dict(by_alias=True)
    )# is the proxy function that will be called (u can validate the variables here)
    return operation(**x.data) # Serialize the result

```
  
  Subscriptions are supported and will map to an async iterator.

