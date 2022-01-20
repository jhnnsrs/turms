# turms

[![codecov](https://codecov.io/gh/jhnnsrs/turms/branch/master/graph/badge.svg?token=UGXEA2THBV)](https://codecov.io/gh/jhnnsrs/turms)

### DEVELOPMENT

# Insipiration

Baldr is a pure python implementation of the awesome graphql-codegen library, following a simliar extensible design.
It makes heavy use of pydantic and its serialization capablities and provides fully typed querys, mutations and subscriptions

## Supports

- Documents
- Fragments
- Enums
- Query Functions

## Featurs

- Fully Modular (agnostic of graphql engine)
- Specify type mixins, baseclasses...
- Fully Support type hints for variables (Pylance, VSCode)

## Installation

```bash
pip install turms
```

## Usage

Open your workspace (create a virtual env), in the root folder

```bash
turms init
```

This creates a configuration file in the working directory, edit this to reflect your
settings (see Configuration)

```bash
turms gen
```

Generate beautifully typed Operations, Enums,...

## Why Turms

In Etruscan religion, Turms (usually written as 𐌕𐌖𐌓𐌌𐌑 Turmś in the Etruscan alphabet) was the equivalent of Roman Mercury and Greek Hermes, both gods of trade and the messenger god between people and gods.
