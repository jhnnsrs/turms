# turms

[![codecov](https://codecov.io/gh/jhnnsrs/turms/branch/master/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/jhnnsrs/turms)
[![PyPI version](https://badge.fury.io/py/turms.svg)](https://pypi.org/project/turms/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/turms/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/turms.svg)](https://pypi.python.org/pypi/turms/)
[![PyPI status](https://img.shields.io/pypi/status/turms.svg)](https://pypi.python.org/pypi/turms/)
[![PyPI download month](https://img.shields.io/pypi/dm/turms.svg)](https://pypi.python.org/pypi/turms/)

### DEVELOPMENT

## Inspiration

Turms is a pure python implementation of the awesome graphql-codegen library, following a simliar extensible design.
It makes heavy use of pydantic and its serialization capablities and provides fully typed querys, mutations and subscriptions

## Supports

- Documents
- Fragments
- Enums
- Operations
- Operation Functions
- Scalar (mapping to python equivalent)

## Features

- Fully Modular (agnostic of graphql transport)
- Tries to minimise Class Generation if using Fragments
- Autocollapsing operation (if mutation or query has only one operation) functions
- Specify type mixins, baseclasses...
- Fully Support type hints for variables (Pylance)
- Compliant with graphl-config

## Companion Library

If you are searching for an Apollo-like GraphQL Client you can check out [rath](https://github.com/jhnnsrs/rath), that works especially
well with turms.

## Installation

```bash
pip install turms
```

## Configuration

Turms configuration is compliant with the graphql-config specification, allowing interoperability with other frameworks.

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

Turms configuration is based on plugins that can be configured in the graphql.config. There exist three major classes:

### Stylers

Stylers are responsible for applying different styles to the class names and field names (e.g. snakecasing of graphqls pascalcase),
they are chained in order of notation in the graphql config (they receive the output of the last styler). Turms takes care of automatically
aliasing these names if they are not the same as the graphql style)

### Plugins

Plugins are the generators of code, that traverse through the direcotry and ad new ast nodes to the global tree. Examplary pluings are:

- turms.plugins.enums.EnumsPlugin
- turms.plugins.inputs.InputsPlugin
- turms.plugins.fragments.FragmentsPlugin
- turms.plugins.operation.OperationsPlugin
- turms.plugins.funcs.OperationsFuncPlugin

## Processors

Processors take the generated code (already a string), and can parse this code. (e.g. black processor for enforcing black style formatting) or isort of sorting imports.
Includes Processors are

- turms.processor.black.BlackProcessor
- turms.processor.isort.IsortProcessor

## Usage

Open your workspace (create a virtual env), in the root folder

```bash
turms init
```

This creates a graphql-config compliant configuration file in the working directory, edit this to reflect your settings (see Configuration)

```bash
turms gen
```

Generate beautifully typed Operations, Enums,...

### Why Turms

In Etruscan religion, Turms (usually written as 𐌕𐌖𐌓𐌌𐌑 Turmś in the Etruscan alphabet) was the equivalent of Roman Mercury and Greek Hermes, both gods of trade and the **messenger** god between people and gods.

## Transport Layer

Turms does not come with a default transport layer, but by specifiyng custom queries classes you can easily incorporate your logic (look at turms.types.herre for inspiration)

## Examples

This github repository also contains an example graphql.config.yaml with the public SpaceX api, as well as a sample of the generated api.

## Experimental

```bash
turms watch $PROJECT_NAME
```

Turms watch is able to automatically monitor your graphql folder for changes and autogenerate the api on save again.
Requires additional dependency for watchdog

```bash
pip install turms[watch]
```
