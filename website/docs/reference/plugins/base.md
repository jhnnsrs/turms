---
sidebar_label: base
title: plugins.base
---

## Plugin Objects

```python
class Plugin(BaseModel)
```

Base class for all plugins

Plugins are the workhorse of turms. They are used to generate python code, according
to the GraphQL schema. You can use plugins to generate python code for your GraphQL
schema. THe all received the graphql schema and the config of the plugin.

