import json


def is_true(val):
    value = str(val).strip().upper()
    if value in ("1", "TRUE", "T", "Y", "YES"):
        return True
    return False


def is_false(val):
    value = str(val).strip().upper()
    if value in ("0", "FALSE", "F", "N", "NO", "NONE", ""):
        return True
    return False


def is_bool(val):
    """
    Check whether a string can be convert to bool.
    :param val: value as string.
    :return: `True` if value can be convert to bool else `False`.
    """
    return is_true(val) or is_false(val)


def is_port(port):
    """
    Check whether a port is valid.
    :param port: port to check.
    :return: `True` if port is valid else `False`.
    """
    try:
        return 1 <= int(port) <= 65535
    except ValueError:
        return False


def load_json_file(file_path):
    """
    Load a dict from a JSON file.
    :param file_path: JSON file path.
    :return: A `dict` object.
    """
    with open(file_path, 'r') as file_pointer:
        return json.load(file_pointer)
