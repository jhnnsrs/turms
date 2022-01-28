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

## Config

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
