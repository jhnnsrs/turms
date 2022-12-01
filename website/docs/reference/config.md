---
sidebar_label: config
title: config
---

## PythonType Objects

```python
class PythonType(str)
```

A string that represents a python type. Either a builtin type or a type from a module.

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

#### enabled

Enabling this, will freeze the schema

#### types

The core types (Input, Fragment, Object, Operation) to freeze

#### exclude

List of types to exclude from freezing

#### include

The types to freeze

#### convert\_list\_to\_tuple

Convert GraphQL List to tuple (with varying length)

## GeneratorConfig Objects

```python
class GeneratorConfig(BaseSettings)
```

Configuration for the generator

This is the main generator configuration that allows you to
customize the way the models are generated.

You need to specify the documents that should be parsed
and the scalars that should be used.

#### domain

The domain of the GraphQL API ( will be set as a config variable)

#### out\_dir

The output directory for the generated models

#### generated\_name

The name of the generated file within the output directory

#### documents

The documents to parse. Setting this will overwrite the documents in the graphql config

#### verbose

Enable verbose logging

#### object\_bases

The base classes for the generated objects. This is useful if you want to change the base class from BaseModel to something else

#### interface\_bases

List of base classes for interfaces

#### always\_resolve\_interfaces

Always resolve interfaces to concrete types

#### scalar\_definitions

Additional config for mapping scalars to python types (e.g. ID: str). Can use dotted paths to import types from other modules.

#### freeze

Configuration for freezing the generated models: by default disabled

#### additional\_bases

Additional bases for the generated models as map of GraphQL Type to importable base class (e.g. module.package.Class)

#### additional\_config

Additional config for the generated models as map of GraphQL Type to config attributes

#### force\_plugin\_order

Should the plugins be forced to run in the order they are defined

#### parsers

List of parsers to use. Parsers are used to parse the generated AST and translate it before it is converted to python code

#### plugins

List of plugins to use. Plugins are used to generated the python ast from the graphql documents, objects, etc.

#### processors

List of processors to use. Processor are used to enforce specific styles on the generated python code

#### stylers

List of stylers to use. Style are used to enforce specific styles on the generaded class or fieldnames.

## Extensions Objects

```python
class Extensions(BaseModel)
```

Wrapping class to be able to extract the tums configuraiton

#### turms

The turms configuration

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

#### schema\_url

The schema url or path to the schema file

#### bearer\_token

The bearer token to use for the schema if retrieving it from a remote url

#### documents

The documents (operations,fragments) to parse

#### extensions

The extensions configuration for the project (here resides the turms configuration)

## GraphQLConfigMultiple Objects

```python
class GraphQLConfigMultiple(BaseSettings)
```

Configuration for multiple GraphQL projects

This is the main configuration for multiple GraphQL projects. It is compliant with
the graphql-config specification for multiple projec.

#### projects

The projects that should be parsed. The key is the name of the project and the value is the graphql project

## GraphQLConfigSingle Objects

```python
class GraphQLConfigSingle(GraphQLProject)
```

Configuration for a single GraphQL project

This is the main configuration for a single GraphQL project. It is compliant with
the graphql-config specification for a single project.

