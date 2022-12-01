---
sidebar_label: utils
title: utils
---

#### target\_from\_node

```python
def target_from_node(node: FieldNode) -> str
```

Extacts the field name from a FieldNode. If alias is present, it will be used instead of the name

#### inspect\_operation\_for\_documentation

```python
def inspect_operation_for_documentation(operation: OperationDefinitionNode)
```

Checks for operation level documentatoin

#### generate\_typename\_field

```python
def generate_typename_field(typename: str, registry: ClassRegistry)
```

Generates the typename field a specific type, this will be used to determine the type of the object in the response

#### generate\_config\_class

```python
def generate_config_class(graphQLType: GraphQLTypes,
                          config: GeneratorConfig,
                          typename: str = None)
```

Generates the config class for a specific type

It will append the config class to the registry, and set the frozen
attribute for the class to True, if the freeze config is enabled and
the type appears in the freeze list.

It will also add config attributes to the class, if the type appears in
&#x27;additional_config&#x27; in the config file.

#### parse\_documents

```python
def parse_documents(client_schema: GraphQLSchema, scan_glob) -> DocumentNode
```



#### parse\_value\_node

```python
def parse_value_node(
        value_node: ValueNode) -> Union[None, str, int, float, bool]
```

Parses a Value Node into a Python value
using standard types

**Arguments**:

- `value_node` _ValueNode_ - The Argument Value Node
  

**Raises**:

- `NotImplementedError` - If the Value Node is not supported
  

**Returns**:

  Union[None, str, int, float, bool]: The parsed value

