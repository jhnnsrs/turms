---
sidebar_label: ruff
title: processors.ruff
---

## RuffProcessor Objects

```python
class RuffProcessor(Processor)
```

A processor that uses ruff to format and/or fix the generated python code.

Ruff is an extremely fast python linter and code formatter. It needs to be
separately installed via &#x27;pip install ruff&#x27;.

Configuration options:

- `format` (default `true`): run `ruff format` to enforce a consistent style.
- `fix` (default `false`): run `ruff check --fix` to apply auto-fixable lint rules (e.g. removing unused imports).
