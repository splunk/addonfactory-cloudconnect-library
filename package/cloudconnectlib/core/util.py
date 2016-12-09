import json
import os
import sys


def register_module(new_path):
    """ register_module(new_path): adds a directory to sys.path.
    Do nothing if it does not exist or if it's already in sys.path.
    """
    if not os.path.exists(new_path):
        return

    new_path = os.path.abspath(new_path)
    if sys.platform == 'win32':
        new_path = new_path.lower()

    for x in sys.path:
        x = os.path.abspath(x)
        if sys.platform == 'win32':
            x = x.lower()
        if new_path in (x, x + os.sep):
            return
    sys.path.append(new_path)

from ..splunktalib.common import util


def is_bool(val):
    """Check whether a string can be convert to bool.
    :param val: value as string.
    :return: `True` if value can be convert to bool else `False`.
    """
    return util.is_true(val) or util.is_false(val)


def is_port(port):
    """Check whether a port is valid.
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
