---
sidebar_position: 1
sidebar_label: "Plugins"
---

# Plugins

Plugins are the heart of turms. They are generating the actual
python AST (Abstract Syntax Tree), that will be used for code generation.

```mermaid
flowchart LR;
id0(Documents)-->|gql&schema|id1(Plugin)
id0(Documents)-->|gql&schema|id2(Plugin)
id0(Documents)-->|gql&schema|id3(Plugin)
id1(Plugin)-->|python.AST|id50(Appender)
id2(Plugin)-->|python.AST|id50(Appender)
id3(Plugin)-->|python.AST|id50(Appender)
id50(Appender)-->|str|id61(Processor)
id50(Appender)-->|str|id62(Processor)
id61(Processor)-->id100(generated.py)
id62(Processor)-->id100(generated.py)

```

They closely work with stylers to ensure your favourite code style gets respected.

## Generation

Plugins are called sequentially and the output will be appended to the global ast.Tree,
Plugins can also register imports and register references to their generated code for
following plugins to find (check ClassRegistry)
