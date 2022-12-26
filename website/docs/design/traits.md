---
sidebar_position: 1
sidebar_label: "Traits"
title: "Traits"
---

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

## Why use traits?

- Addin-Logic: With the traits approach you can easily add type specficig logic to your graphql types, e.g adding fields that require some sort of computation, or add additional methods. This means that even in complex nested documents you will be able to have access to the model specific logic.

- Instance Checks: As traits are added baseclasses, you will be able to check them through `isinstance(t, MixinName)`