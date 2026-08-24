---
sidebar_position: 1
sidebar_label: "Parsers"
---

# Parsers

Parsers are plugings that take the Python AST and process it before it is unparsed to a
string.They are great for ensuring compatibility between different python versions, backporting
more modern python constructs to older versions.

No parsers ship with turms. The stage is an extension point: point a `parsers` entry's `type`
at any importable subclass of `turms.parsers.base.Parser`.

The `polyfill` parser was removed in turms 2.0. It only ever backported `Literal` to
`typing_extensions` for a python 3.7 target, and pydantic v2 -- the only target turms
generates for -- has never supported python 3.7.