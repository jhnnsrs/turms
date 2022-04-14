import os

DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative_glob(path):
    return DIR_NAME + path


def generated_module_is_executable(module: str) -> bool:
    exec_locals = {}
    exec_globals = {}

    imports = [line for line in module.split("\n") if line.startswith("from")]
    for import_ in imports:
        exec(import_, exec_globals, exec_locals)
    exec_globals.update(exec_locals)

    try:
        exec(module, exec_globals)
    except:
        return False
    return True
