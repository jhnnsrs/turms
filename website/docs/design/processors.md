---
sidebar_position: 1
sidebar_label: "Processors"
---

# Processors

Processors sit at the end of the generaiton pipeline

```mermaid
flowchart LR;
    id0(Plugin1)-->|AST|id1(Plugin2)
    id1(Plugin2)-->|AST|id2(Plugin3)
    id2(Plugin3)-->|AST|id3(Composer)
    id3(Composer)-->|ast.unparse|id3(Composer)
    id3(Composer)-->|str|id4(Processor)
    id4(Processor)-->|str|id5(Processor 2)
    id5(Processor 2)-->|str|id6(FileOut)
```

They are the entrypoint for linters, import sorting and application
of code styles.

## Included Processors

Turms comes included with two processors that rely on external dependencies:

- **Black** Applys the black codestyle
- **ISort** Sort the imports according to isort
