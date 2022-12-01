---
sidebar_label: helpers
title: helpers
---

#### import\_class

```python
def import_class(module_path, class_name)
```

Import a module from a module_path and return the class

#### import\_string

```python
def import_string(dotted_path)
```

Import a dotted module path and return the attribute/class designated by the
last name in the path. Raise ImportError if the import failed. Simliar to
djangos import_string, but without the cache.

#### introspect\_url

```python
def introspect_url(schema_url: str,
                   bearer_token: Optional[str] = None) -> Dict[str, Any]
```

Introspect a GraphQL schema using introspection query

**Arguments**:

- `schema_url` _str_ - The Schema url
- `bearer_token` _str, optional_ - A Bearer token. Defaults to None.
  

**Raises**:

- `GenerationError` - An error occurred while generating the schema.
  

**Returns**:

- `dict` - The introspection query response.

#### build\_schema\_from\_introspect\_url

```python
def build_schema_from_introspect_url(
        schema_url: str,
        bearer_token: Optional[str] = None) -> graphql.GraphQLSchema
```

Introspect a GraphQL schema using introspection query

**Arguments**:

- `schema_url` _str_ - The Schema url
- `bearer_token` _str, optional_ - A Bearer token. Defaults to None.
  

**Raises**:

- `GenerationError` - An error occurred while generating the schema.
  

**Returns**:

- `graphql.GraphQLSchema` - The parsed GraphQL schema.

#### build\_schema\_from\_glob

```python
def build_schema_from_glob(glob_string: str)
```

Build a GraphQL schema from a glob string

