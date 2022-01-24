# turms

[![codecov](https://codecov.io/gh/jhnnsrs/turms/branch/master/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/jhnnsrs/turms)
[![PyPI version](https://badge.fury.io/py/turms.svg)](https://pypi.org/project/turms/)

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

## Features

- Fully Modular (agnostic of graphql transport)
- Tries to minimise Class Generation if using Fragments
- Autocollapsing operation (if mutation or query has only one operation) functions
- Specify type mixins, baseclasses...
- Fully Support type hints for variables (Pylance)
- Compliant with graphl-config

## Installation

```bash
pip install turms
```

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

## Experimental

```bash
turms watch $PROJECT_NAME
```

Turms watch is able to automatically monitor your graphql folder for changes and autogenerate the api on save again.
Requires additional dependency for watchdog

```bash
pip install turms[watch]
```
