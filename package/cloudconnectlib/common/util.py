import json
from ..splunktalib.common import util
from ..splunktacollectorlib.common import log as stulog
from ..splunktacollectorlib.data_collection import ta_helper as th
from .lib_util import get_mod_input_script_name
from solnlib.modular_input.event import XMLEvent


def is_valid_bool(val):
    """Check whether a string can be convert to bool.
    :param val: value as string.
    :return: `True` if value can be convert to bool else `False`.
    """
    return util.is_true(val) or util.is_false(val)


def is_true(val):
    return util.is_true(val)


def is_valid_port(port):
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


def format_events(raw_events, time=None,
                  index=None, host=None, source=None, sourcetype=None,
                  stanza=None, unbroken=False, done=False):
    return XMLEvent.format_events(XMLEvent(data, time=time,
                                           index=index, host=host,
                                           source=source,
                                           sourcetype=sourcetype,
                                           stanza=stanza, unbroken=unbroken,
                                           done=done) for data in
                                  raw_events)


def reset_logger(stanza_name, logging_level, log_suffix="modinput"):
    script_name = get_mod_input_script_name()
    logger_name = script_name + "_" + th.format_name_for_file(stanza_name)
    stulog.reset_logger(logger_name)
    stulog.set_log_level(logging_level)
