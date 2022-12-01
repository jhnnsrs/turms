---
sidebar_label: base
title: stylers.base
---

## Styler Objects

```python
class Styler(BaseModel)
```

Base class for all stylers

Stylers are used style the classnames function names of the generated python code.
YOu can enforce specific code styles on the generated python code like (snake_case or camelCase)

If you change the fieldname of a field in the GraphQL schema, the stylers will be used to
style the fieldname in the generated python code and an alias will be added to the field.

## BaseStyler Objects

```python
class BaseStyler(Styler)
```

A styler that uses no styling on the generated python code.

