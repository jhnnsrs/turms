---
sidebar_position: 3
sidebar_label: "Fragments"
---

# Fragments

Enums generates python objects from Graphql Fragments

### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.inputs.InputsPlugin
            fragment_bases: #List[str] = None
            fragments_glob: #Optional[str] a glob for fragments
```
