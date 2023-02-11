---
sidebar_position: 2
sidebar_label: "InputType"
---

# InputType

InputType generates python objects from Graphql InputTypes

### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.inputs.InputsPlugin
            inputtype_bases: #List[str] = ["pydantic.BaseModel"]
            skip_underscore: #bool = True
```
