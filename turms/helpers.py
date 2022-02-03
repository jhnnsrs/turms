import copy
import os
import sys
from importlib import import_module
from importlib.util import find_spec as importlib_find


def import_class(module_path, class_name):
    module = import_module(module_path)
    return getattr(module, class_name)


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed. Simliar to
    djangos import_string, but without the cache.
    """

    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError(f"{dotted_path} doesn't look like a module path") from err

    try:
        return import_class(module_path, class_name)
    except AttributeError as err:
        raise ImportError(
            f"{module_path} does not define a {class_name} attribute/class"
        ) from err
