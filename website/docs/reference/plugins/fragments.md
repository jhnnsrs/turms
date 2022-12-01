---
sidebar_label: fragments
title: plugins.fragments
---

## FragmentsPlugin Objects

```python
class FragmentsPlugin(Plugin)
```

Plugin for generating fragments from
documents

The fragments plugin will generate classes for each fragment. It loads the documents,
scans for fragments and generates the classes.

If encountering a fragment on an interface it will generate a BASE class for that interface
and then generate a class for each type referenced in the fragment. They will all inherit
from the base class. The true type will be determined at runtime as all of the potential subtypes
will be in the same union.

