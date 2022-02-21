---
sidebar_label: utils
title: types.utils
---

#### clean\_dict

```python
def clean_dict(obj, func)
```

This method scrolls the entire &#x27;obj&#x27; to delete every key for which the &#x27;callable&#x27; returns

True

**Arguments**:

- `obj`: a dictionary or a list of dictionaries to clean
- `func`: a callable that takes a key in argument and return True for each key to delete

