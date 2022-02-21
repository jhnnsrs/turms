---
sidebar_label: operation
title: types.operation
---

## OperationMeta Objects

```python
class OperationMeta(ModelMetaclass)
```

The Model Meta class extends the Pydantic Metaclass and adds in
syncrhonous and asynchronous Managers. These Managers allow direct
interaction with serverside Objects mimicking the Django ORM Scheme
(https://docs.djangoproject.com/en/3.2/topics/db/queries/) it
also registeres the Model as a potential serializer.

Every Class using this metaclass has to subclass pydantic.BaseModel and
implement a Meta class with the identifier attribute set to a cleartext
identifier on the arkitekt platform.

If this identifier does not exist, the serializer can potentially be auto
registered with the platform according to the apps name

**Arguments**:

- `ModelMetaclass` _[type]_ - [description]

