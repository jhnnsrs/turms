---
sidebar_label: helpers
title: helpers
---

#### import\_string

```python
def import_string(dotted_path)
```

Import a dotted module path and return the attribute/class designated by the
last name in the path. Raise ImportError if the import failed. Simliar to
djangos import_string, but without the cache.

