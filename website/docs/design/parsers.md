---
sidebar_position: 1
sidebar_label: "Parsers"
---

# Parsers

Parsers are plugings that take the Python AST and process it before it is unparsed to a
string.They are great for ensuring compatibility between different python versions, backporting
more modern python constructs to older versions.

Turms comes included with two parsers included

- *polyill* The polyfill parser is used to polyfill the generated python code with additional imports and code to make it compatible with older python versions.(Right now it only supports polyfils for python 3.7 )