---
sidebar_label: base
title: parsers.base
---

## Parser Objects

```python
class Parser(BaseModel)
```

Base class for all parsers

Parsers are used to parse the AST of the generated python code. They can be used to
modify the AST before it is written to the file.

