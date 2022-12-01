---
sidebar_label: registry
title: registry
---

## ClassRegistry Objects

```python
class ClassRegistry(object)
```

Class Registry is responsible for keeping track of all the classes that are generated
as well as their names. It also keeps track of all the imports that are required for the
generated code to work, as well as all the forward references that are required
for the generated code to work (i.e. when a class references another class that has not
yet been defined). Class Registry provides a facade to the rest of the code to abstract
the logic behind the stylers.

