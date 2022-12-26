---
sidebar_position: 1
sidebar_label: "Processors"
---

# Processors

Processors sit at the end of the processing pipeline and are responsible for performaing string
operations on the generated code.

## Included Processors

Turms comes included with two processors that rely on external dependencies:

- **Black** Applys the black codestyle
- **ISort** Sort the imports according to isort
- **Merge** Tries to merge the code (and comments) of the previous code generation run, with the newly generated code updating only schema fields
