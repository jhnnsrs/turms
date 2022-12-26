---
sidebar_position: 5
sidebar_label: "Strawberry Schema"
---

# Strawberry

This plugin generates a fully fledged strawberry schema from your
SDL schema.


### Default Configuration

```yaml
project:
  default:
    schema: ...
    extensions:
      turms:
        plugins:
          - type: turms.plugins.strawberry.StrawberryPlugin
            generate_directives: True # should we generate directives
            generate_scalars: True # should we generate scalars
            builtin_directives: # directives that are builtin and will not be generated through strawberry.directive
               - "include"
               - "skip"
               - "deprecated"
               - "specifiedBy"
            builtin_scalars:  #scalars that will not be created through stawberry.scalar
              - "String",
              - "Boolean"
              - "DateTime"
              - "Int"
              - "Float"
              - "ID"
            generate_enums: True # should we generate enums
            generate_types: True # should we generate types (objects, queries, mutations, subscriptiosn)
            generate_inputs: True # should we generate input types
            types_bases: [] # additional type bases
            inputtype_bases: [] # additional inputtype bases
            skip_underscore: False # skip generated underscored types
            skip_double_underscore: True # skip generatind double underscored types
```



