---
sidebar_label: errors
title: errors
---

## TurmsError Objects

```python
class TurmsError(Exception)
```

Base class for all Turms errors

## RegistryError Objects

```python
class RegistryError(Exception)
```

Base class for all registry errors

## NoScalarFound Objects

```python
class NoScalarFound(RegistryError)
```

Raised when no scalar is found for a given type. Needs to provided by additional scalars

## NoInputTypeFound Objects

```python
class NoInputTypeFound(RegistryError)
```

Raised when no input type is found for a given type. Often raised if the input plugin is not loaded, and operations
use input tyes

## NoEnumFound Objects

```python
class NoEnumFound(RegistryError)
```

Raised when no enum is found for a given type. Often raised if the enum plugin is not loaded, and operations or fragments
use enums

## GenerationError Objects

```python
class GenerationError(TurmsError)
```

Base class for all generation errors

