---
sidebar_label: config
title: config
---

## FreezeConfig Objects

```python
class FreezeConfig(BaseSettings)
```

Configuration for freezing the generated pydantic
models

This is useful for when you want to generate the models
that are faux immutable and hashable by default. The configuration
allows you to customize the way the models are frozen and specify
which types (operation, fragment, input,...) should be frozen.

## GeneratorConfig Objects

```python
class GeneratorConfig(BaseSettings)
```

Configuration for the generator

This is the main generator configuration that allows you to
customize the way the models are generated.

You need to specify the documents that should be parsed
and the scalars that should be used.

## Extensions Objects

```python
class Extensions(BaseModel)
```

Wrapping class to be able to extract the tums configuraiton

## GraphQLProject Objects

```python
class GraphQLProject(BaseSettings)
```

Configuration for the GraphQL project

This is the main configuration for one GraphQL project. It is compliant with
the graphql-config specification. And allows you to specify the schema and
the documents that should be parsed.

Turm will use the schema and documents to generate the python models, according
to the generator configuration under extensions.turms

## GraphQLConfigMultiple Objects

```python
class GraphQLConfigMultiple(BaseSettings)
```

Configuration for multiple GraphQL projects

This is the main configuration for multiple GraphQL projects. It is compliant with
the graphql-config specification for multiple projec.

## GraphQLConfigSingle Objects

```python
class GraphQLConfigSingle(GraphQLProject)
```

Configuration for a single GraphQL project

This is the main configuration for a single GraphQL project. It is compliant with
the graphql-config specification for a single project.

