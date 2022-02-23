---
sidebar_position: 1
sidebar_label: "Traits"
---

### Traits

Traits are just mixins. If you want to specify extra logic that should be added to a specific type in your schema you can do so by specifing "additional_bases" in the configuration setting:

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        additional_bases:
          $YOUR_GRAHQL_TYPE:
            - path.to.additional.Base1
            - path.to.additional.Base2
```
