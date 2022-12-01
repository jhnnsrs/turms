---
sidebar_label: enums
title: plugins.enums
---

## EnumsPlugin Objects

```python
class EnumsPlugin(Plugin)
```

The Enum plugin generates python enums from the GraphQL schema.

It does not need documents but generates every enum from the loaded schema.

By providing a config, you can skip enums that start with an underscore and
prepend and append strings to the generated enums.

