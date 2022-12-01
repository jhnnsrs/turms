---
sidebar_label: objects
title: plugins.objects
---

## ObjectsPlugin Objects

```python
class ObjectsPlugin(Plugin)
```

Generate Pydantic models for GraphQL objects

This plugin generates Pydantic models for GraphQL ObjectTypes and Interfaces in your graphql schema.

Attention: This plugin is not made for client side usage. Most likely you are looking for the
operations, fragments and funcs plugin (that generates client side validation and query function
for your documents (your operations, fragments and queries).

