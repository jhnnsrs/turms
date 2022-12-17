from pydantic import BaseModel
from enum import Enum
import libcst as cst
from collections import OrderedDict

# the one we want to merge into
# load beast_two.py as a ast.Module
with open("beast_two.py") as f:
    existing_module = cst.parse_module(f.read())

# load beasts.py as a ast.Module

# the one we want to merge from
with open("beasts.py") as f:
    new_module = cst.parse_module(f.read())


symbols = OrderedDict()

existing_symbols = set()
implemented_symbols = []
new_symbols = set()

new_body = []


def merge_functions(generated: cst.FunctionDef, existing: cst.FunctionDef):
    # merge the two functions

    # we want to merge the body of the new function into the existing one

    new_def = generated.with_changes(body=existing.body)
    return new_def


def merge_statements(
    generead: cst.SimpleStatementLine, existing: cst.SimpleStatementLine
):
    # merge the two statements

    # we want to merge the body of the new statement into the existing one

    new_def = generead.with_changes(body=existing.body)
    return new_def


def retrieve_symbol_name(simple_statement: cst.SimpleStatementLine):
    for node in simple_statement.body:
        if isinstance(node, cst.AnnAssign):
            return node.target.value
    else:
        return None


def merge_class(generated: cst.ClassDef, existing: cst.ClassDef):
    # merge the two classes
    body_symbols = OrderedDict()
    body_implemented_symbols = []
    body_symbol_position = OrderedDict()

    generated_indented_block = generated.body

    for node in generated_indented_block.body:
        if isinstance(node, cst.FunctionDef):
            body_symbols[node.name.value] = node

        if isinstance(node, cst.SimpleStatementLine):
            x = retrieve_symbol_name(node)
            if retrieve_symbol_name(node) is not None:
                body_symbols[x] = node

    existing_indented_block = existing.body

    new_body = []

    for node in existing_indented_block.body:
        if isinstance(node, cst.SimpleStatementLine):
            name = retrieve_symbol_name(node)
            if name is not None:
                if name in body_symbols:
                    new_body.append(merge_statements(body_symbols[name], node))
                    body_symbol_position[name] = len(new_body)
                    body_implemented_symbols.append(name)
                else:
                    new_body.append(node)
            else:
                new_body.append(node)

        elif isinstance(node, cst.FunctionDef):
            if node.name.value in body_symbols:
                print("found overlapping class method", node.name.value)
                x = body_symbols[node.name.value]
                new_body.append(merge_functions(x, node))
                body_implemented_symbols.append(node.name.value)
                body_symbol_position[node.name.value] = len(new_body)
            else:
                new_body.append(node)

        else:
            new_body.append(node)

    # add the missing classes at the right position

    body_missing_symbols = [
        key for key in body_symbols.keys() if key not in body_implemented_symbols
    ]

    print("Adding missing bodysymbols", body_missing_symbols)

    beforemap = {}  # a map index and a list of symbols to insert before
    aftermap = {}

    # add the missing classes at the right position
    last_key = None
    for existingkey in body_implemented_symbols:
        last_key = existingkey
        for key, value in body_symbols.items():
            if existingkey == key:
                break
            if key in body_missing_symbols:
                print("found missing bodysymbol", key, "before", existingkey)
                body_missing_symbols.remove(key)
                beforemap.setdefault(body_symbol_position[existingkey], []).append(
                    key
                )  # we need to reverse

    if last_key is not None:
        aftermap[body_symbol_position[last_key]] = body_missing_symbols

    updated_body = []
    for index, node in enumerate(new_body):
        if (index + 1) in beforemap:
            for missingkey in beforemap[index + 1]:
                updated_body.append(body_symbols[missingkey])
        updated_body.append(node)
        if index in aftermap:
            for missingkey in aftermap[index]:
                updated_body.append(body_symbols[missingkey])

    if last_key is None:
        print("Never found a implemented symbol. Append all missing symbols")
        for missingkey in body_missing_symbols:
            updated_body.append(body_symbols[missingkey])

    new_class = existing.with_changes(
        body=existing_indented_block.with_changes(body=updated_body)
    )

    return new_class


# merge the two ast.Module
for node in new_module.body:

    if isinstance(node, cst.ClassDef):
        symbols[node.name.value] = node
        new_symbols.add(node.name.value)

    if isinstance(node, cst.FunctionDef):
        symbols[node.name.value] = node
        new_symbols.add(node.name.value)


symbol_position = {}

for node in existing_module.body:
    if isinstance(node, cst.ClassDef):
        print("found class", node.name.value)
        if node.name.value in symbols:
            print("found overlapping class", node.name.value)
            x = symbols[node.name.value]
            # merge the two classes
            new_body.append(merge_class(x, node))
            symbol_position[node.name.value] = len(new_body)
            implemented_symbols.append(node.name.value)
        else:
            new_body.append(node)

    elif isinstance(node, cst.FunctionDef):
        print("found function", node.name.value)
        if node.name.value in symbols:
            print("found overlapping function", node.name.value)
            # merge the two functions
            x = symbols[node.name.value]
            new_body.append(merge_functions(x, node))
            symbol_position[node.name.value] = len(new_body)
            implemented_symbols.append(node.name.value)
        else:
            new_body.append(node)

    else:
        new_body.append(node)


# add the missing classes at the right position

missing_symbols = [key for key in symbols.keys() if key not in implemented_symbols]


print("Adding missing symbols", missing_symbols)

beforemap = {}  # a map index and a list of symbols to insert before
aftermap = {}

# add the missing classes at the right position
last_key = None
for existingkey in implemented_symbols:
    last_key = existingkey
    for key, value in symbols.items():
        if existingkey == key:
            break
        if key in missing_symbols:
            print("found missing symbol", key, "before", existingkey)
            missing_symbols.remove(key)
            beforemap.setdefault(symbol_position[existingkey], []).append(
                key
            )  # we need to reverse

if last_key is not None:
    aftermap[symbol_position[last_key]] = missing_symbols

updated_body = []
for index, node in enumerate(new_body):
    if (index + 1) in beforemap:
        for missingkey in beforemap[index + 1]:
            updated_body.append(symbols[missingkey])
    updated_body.append(node)
    if index in aftermap:
        for missingkey in aftermap[index]:
            updated_body.append(symbols[missingkey])

if last_key is None:
    print("Never found a implemented symbol. Append all missing symbols")
    for missingkey in missing_symbols:
        updated_body.append(symbols[missingkey])


md = cst.Module(body=updated_body)

with open("new_beasts.py", "w") as f:
    f.write(md.code)
