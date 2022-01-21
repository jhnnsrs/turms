def clean_dict(obj, func):
    """
    This method scrolls the entire 'obj' to delete every key for which the 'callable' returns
    True

    :param obj: a dictionary or a list of dictionaries to clean
    :param func: a callable that takes a key in argument and return True for each key to delete
    """
    if isinstance(obj, dict):
        # the call to `list` is useless for py2 but makes
        # the code py2/py3 compatible

        for key, value in dict(**obj).items():
            if func(key, value):
                del obj[key]
            else:
                clean_dict(obj[key], func)
    elif isinstance(obj, list):
        for i in reversed(range(len(obj))):
            clean_dict(obj[i], func)

    else:
        # neither a dict nor a list, do nothing
        pass
