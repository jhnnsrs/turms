---
sidebar_position: 1
sidebar_label: "Enums"
---

# Enums

Enums generates python enums from Graphql Enums

### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.enums.EnumsPlugin
            skip_underscore: True
            prepend: ""
            append: ""
```

#### Code Example

```python
class Order_by(str, Enum):
    """column ordering options"""

    asc = "asc"
    "in the ascending order, nulls last"
    asc_nulls_first = "asc_nulls_first"
    "in the ascending order, nulls first"
    asc_nulls_last = "asc_nulls_last"
    "in the ascending order, nulls last"
    desc = "desc"
    "in the descending order, nulls first"
    desc_nulls_first = "desc_nulls_first"
    "in the descending order, nulls first"
    desc_nulls_last = "desc_nulls_last"
    "in the descending order, nulls last"
```
