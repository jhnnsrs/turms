---
sidebar_label: command
title: processors.command
---

## CommandProcessor Objects

```python
class CommandProcessor(Processor)
```

A processor that pipes the generated python code through an arbitrary command.

The generated code is sent to the command&#x27;s stdin and the (post)processed code is read
back from its stdout. This is a generic escape hatch to run any external formatter or
tool without a dedicated processor, for example running ruff via `uvx`:

```yaml
processors:
  - type: turms.processors.command.CommandProcessor
    command: "uvx ruff format -"
```

The `command` option accepts either a single string (split shell-style) or a list of
arguments, e.g. `["uvx", "ruff", "format", "-"]`.
