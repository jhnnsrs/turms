---
sidebar_label: operations
title: plugins.operations
---

## OperationsPlugin Objects

```python
class OperationsPlugin(Plugin)
```

&quot; Generate operations as classes

This plugin created classes for operations. It will scan your documents and create classes for each operation.
The class will have a `document` attribute that contains the query document, as well as contained &quot;Arguments&quot; class
with the variables for the operation.

This allows for the serialization of values in both directions.

If you want to generate python functions instead, use the `funcs` plugin in ADDITION to this plugin.

