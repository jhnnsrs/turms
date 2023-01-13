# turms

[![codecov](https://codecov.io/gh/jhnnsrs/turms/branch/master/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/jhnnsrs/turms)
[![PyPI version](https://badge.fury.io/py/turms.svg)](https://pypi.org/project/turms/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/turms/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/turms.svg)](https://pypi.python.org/pypi/turms/)
[![PyPI status](https://img.shields.io/pypi/status/turms.svg)](https://pypi.python.org/pypi/turms/)
[![PyPI download month](https://img.shields.io/pypi/dm/turms.svg)](https://pypi.python.org/pypi/turms/)

## Goal

Turms is a `graphql-codegen` inspired code generator for python that generates typed and serializable python code from your graphql schema and documents. Just define your query in standard graphql syntax and let turms create fully typed queries/mutation and subscriptions, that you can use in your favourite IDE.

Turms allows you to easily generate both server-side and client-side code for your GraphQL API.

### Schema (Server) Generation:

Can generate the following types from your graphql SDL schema:

- Enums
- Inputs
- Objects
- Scalars
- Directives

Sepcific generation supported for:

- [x] Strawberry
- [ ] Graphene

### Documents (Client) Generation

Can generate the following pydantic models from your graphql documents:

- Enums
- Inputs
- Scalars
- Fragments
- Operations

## Features

- Fully typed, fully documented code generation
- Schema and Document based code generation
- Compatible with popular graphql libraries (strawberry, gql, rath, etc.)
- Support for custom scalars, custom directives, ...
- Powerful plugin system (e.g. custom Linting, custom formatting, etc.)
- Operation functions like query, mutation, subscription (e.g. `data= get_capsules()`)
- Compliant with graphl-config
- Code migration support (trying to merge updates into existing code)

## Installation

```bash
pip install turms
```

turms is a pure development library and will not introduce any dependency on itself into your
code, so we recommend installing turms as a development dependency.

```bash
poetry add -D turms

```

As of now turms only supports python 3.9 and higher (as we rely on ast unparsing)

## Configuration

Turms relies on and complies with [graphql-config](https://www.graphql-config.com/docs/user/user-introduction) and searches your current working dir for the graphql-config file.

### Document based generation

Based on pydantic models

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

### Schema based generation

Based on strawberry models

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

### Usage

Once you have configured turms you can generate your code by running

```bash
turms gen
```

### Why Turms

In Etruscan religion, Turms (usually written as 𐌕𐌖𐌓𐌌𐌑 Turmś in the Etruscan alphabet) was the equivalent of Roman Mercury and Greek Hermes, both gods of trade and the **messenger** god between people and gods.

## Transport Layer

Turms does _not_ come with a default transport layer but if you are searching for an Apollo-like GraphQL Client you can check out [rath](https://github.com/jhnnsrs/rath), that works especially well with turms.

## Examples

This github repository also contains some examples on how to use turms with popular libraries in the graphql ecosystem.
