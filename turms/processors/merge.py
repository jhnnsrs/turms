from pydantic import Field
from turms.processors.base import Processor, ProcessorConfig
import libcst as cst
from collections import OrderedDict
from turms.config import GeneratorConfig
import os

# load beasts.py as a ast.Module


def retrieve_symbol_name(simple_statement: cst.SimpleStatementLine):
    for node in simple_statement.body:
        if isinstance(node, cst.AnnAssign):
            return node.target.value
    else:
        return None


def merge_functions(generated: cst.FunctionDef, existing: cst.FunctionDef):
    # merge the two functions

    # we want to merge the body of the new function into the existing one

    new_def = generated.with_changes(body=existing.body)
    return new_def


def merge_statements(
    generated: cst.SimpleStatementLine, existing: cst.SimpleStatementLine
):
    # merge the two statements

    # we want to merge the body of the new statement into the existing one

    new_def = existing.with_changes(body=generated.body)
    return new_def


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
                    body_symbol_position[name] = len(new_body)
                    new_body.append(merge_statements(body_symbols[name], node))
                    body_implemented_symbols.append(name)
                else:
                    new_body.append(node)
            else:
                new_body.append(node)

        elif isinstance(node, cst.FunctionDef):
            if node.name.value in body_symbols:
                x = body_symbols[node.name.value]
                body_symbol_position[node.name.value] = len(new_body)
                new_body.append(merge_functions(x, node))
                body_implemented_symbols.append(node.name.value)
            else:
                new_body.append(node)

        else:
            new_body.append(node)

    # add the missing classes at the right position

    body_missing_symbols = [
        key for key in body_symbols.keys() if key not in body_implemented_symbols
    ]

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
                body_missing_symbols.remove(key)
                beforemap.setdefault(body_symbol_position[existingkey], []).append(
                    key
                )  # we need to reverse

    if last_key is not None:
        aftermap[body_symbol_position[last_key]] = body_missing_symbols

    updated_body = []
    for index, node in enumerate(new_body):
        if index in beforemap:
            for missingkey in beforemap[index]:
                updated_body.append(body_symbols[missingkey])
        updated_body.append(node)
        if index in aftermap:
            for missingkey in aftermap[index]:
                updated_body.append(body_symbols[missingkey])

    if last_key is None:
        for missingkey in body_missing_symbols:
            updated_body.append(body_symbols[missingkey])

    new_class = existing.with_changes(
        body=existing_indented_block.with_changes(body=updated_body)
    )

    return new_class


class MergeProcessorConfig(ProcessorConfig):
    type: str = "turms.processors.merge.MergeProcessor"


def merge_code(old_code: str, new_code: str, config: MergeProcessorConfig):

    existing_module = cst.parse_module(old_code)
    new_module = cst.parse_module(new_code)

    symbols = OrderedDict()

    implemented_symbols = []
    new_symbols = set()

    new_body = []

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
            if node.name.value in symbols:
                x = symbols[node.name.value]
                # merge the two classes

                symbol_position[node.name.value] = len(new_body)
                new_body.append(merge_class(x, node))
                implemented_symbols.append(node.name.value)
            else:
                new_body.append(node)

        elif isinstance(node, cst.FunctionDef):
            if node.name.value in symbols:
                # merge the two functions
                x = symbols[node.name.value]

                symbol_position[node.name.value] = len(new_body)
                new_body.append(merge_functions(x, node))
                implemented_symbols.append(node.name.value)
            else:
                new_body.append(node)

        else:
            new_body.append(node)

    # add the missing classes at the right position

    missing_symbols = [key for key in symbols.keys() if key not in implemented_symbols]

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
                missing_symbols.remove(key)
                beforemap.setdefault(symbol_position[existingkey], []).append(
                    key
                )  # we need to reverse

    if last_key is not None:
        aftermap[symbol_position[last_key]] = missing_symbols

    updated_body = []
    for index, node in enumerate(new_body):
        if index in beforemap:
            for missingkey in beforemap[index]:
                updated_body.append(symbols[missingkey])
        updated_body.append(node)
        if index in aftermap:
            for missingkey in aftermap[index]:
                updated_body.append(symbols[missingkey])

    if last_key is None:
        for missingkey in missing_symbols:
            updated_body.append(symbols[missingkey])

    md = cst.Module(body=updated_body)

    return md.code


class MergeProcessor(Processor):
    """A processor that merges the newly generated code
    with the existing code in the file.

    This uiliizes a third party library called libcst to
    parse the existing code and the newly generated code
    and then merge them together.

    We need to use libcst because ast.parse does not
    preserve comments and formatting.

    Important:
        This processor is experimental and may not work
        as expected. Please report any issues you find
        on the github repo.

    """

    config: MergeProcessorConfig = Field(default_factory=MergeProcessorConfig)

    def run(self, gen_file: str, config: GeneratorConfig):

        old_generated_file = os.path.join(
            config.out_dir,
            config.generated_name,
        )

        if not os.path.exists(old_generated_file):
            print("No existing generated file found. Skipping merge.")
            return gen_file

        # the one we want to merge into
        with open(old_generated_file) as f:
            existing_code = f.read()

        return merge_code(existing_code, gen_file, self.config)
