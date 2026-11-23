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

Ruff runs with the configuration of the directory turms runs in. The code
turms generates has every argument and return annotated, so under a
strict project configuration (flake8-annotations, pyupgrade, isort,
pyflakes, bugbear) `fix` only has to sort and prune imports. With
`fix` on, a finding ruff cannot fix fails the run: a scalar mapped to
`typing.Any` in `scalar_definitions` puts `Any` into method
signatures (ANN401); map it to a typed alias instead.

Configuration options:

- `format` (default `true`): run `ruff format` to enforce a consistent style.
- `fix` (default `false`): run `ruff check --fix` to apply auto-fixable lint rules (e.g. removing unused imports).
