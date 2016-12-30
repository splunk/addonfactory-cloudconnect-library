import json
import re
import traceback

from jsonpath_rw import parse
from .exceptions import FuncException
from .pipemgr import PipeManager
from ..common import util, log

_logger = log.get_cc_logger()


def regex_match(pattern, source, flags=0):
    """
    Determine whether a string is match a regex pattern.

    :param pattern: regex pattern
    :param source: candidate to match regex
    :param flags: flags for regex match
    :return: `True` if candidate match pattern else `False`
    """
    try:
        return re.match(pattern, source, flags) is not None
    except (ValueError, TypeError, re.error):
        _logger.warning(
            'Unable to match source with pattern=%s, cause=%s',
            pattern,
            traceback.format_exc()
        )
        return False


def regex_not_match(pattern, source, flags=0):
    """
    Determine whether a string is not match a regex pattern.

    :param pattern: regex expression
    :param source: candidate to match regex
    :param flags: flags for regex match
    :return: `True` if candidate not match pattern else `False`
    """
    return not regex_match(pattern, source, flags)


def json_path(source, json_path_expr):
    """ Extract value from string with JSONPATH expression.
    :param json_path_expr: JSONPATH expression
    :param source: string to extract value
    :return: A `list` contains all values extracted
    """
    if isinstance(source, basestring):
        _logger.debug(
            'source expected is a JSON, not %s. Attempt to'
            ' convert it to JSON',
            type(source)
        )
        try:
            source = json.loads(source)
        except ValueError:
            _logger.warning('Unable to load JSON from source.'
                            'Attempt to apply JSONPATH on source directly.')

    try:
        expression = parse(json_path_expr)
        results = [match.value for match in expression.find(source)]
        return results[0] if len(results) == 1 else results
    except:
        _logger.warning(
            'Unable to apply JSONPATH expression "%s" on source,'
            ' cause=%s',
            json_path_expr,
            traceback.format_exc()
        )
    return []


def splunk_xml(candidates, time=None, index=None, host=None, source=None,
               sourcetype=None):
    """
    Wrap a event with splunk xml format.
    :param candidates: data used to wrap as event
    :param time: timestamp which must be empty or a valid float
    :param index: index name for event
    :param host: host for event
    :param source: source for event
    :param sourcetype: sourcetype for event
    :return: A wrapped event with splunk xml format.
    """
    if not isinstance(candidates, (list, tuple)):
        candidates = [candidates]

    time = time or None
    if time:
        try:
            time = float(time)
        except ValueError:
            _logger.warning(
                '"time" %s is expected to be a float, set "time" to None',
                time
            )
            time = None

    return util.format_events(
        candidates,
        time=time,
        index=index,
        host=host,
        source=source,
        sourcetype=sourcetype
    )


def std_output(candidates):
    """ Output a string to stdout.
    :param candidates: List of string to output to stdout or a single string.
    """
    if isinstance(candidates, basestring):
        candidates = [candidates]

    all_str = True
    for candidate in candidates:
        if all_str and not isinstance(candidate, basestring):
            all_str = False
            _logger.warning(
                'The type of data needs to print is "%s" rather than'
                ' basestring',
                type(candidate)
            )
        if not PipeManager().write_events(candidate):
            raise FuncException('Fail to output data to stdout. The Event'
                                ' writer has stopped or encountered exception')

    _logger.debug('Writing events to stdout finished.')
    return True


def json_empty(source, json_path_expr=None):
    """Check whether a JSON is empty.
    :param json_path_expr: A optional jsonpath expression
    :param source: target to extract
    :return: `True` if the result JSON is `{}` or `[]` or `None`
    """
    if not source:
        _logger.debug(
            'JSON to check is empty, treating it as empty: %s',
            source)
        return True

    if json_path_expr:
        source = json_path(json_path_expr, source)
    if not source:
        return True

    if isinstance(source, (dict, list, tuple)):
        return len(source) == 0

    try:
        return len(json.loads(source)) == 0
    except ValueError:
        _logger.warning(
            'Cannot load JSON from string, treating it as not empty')
        return False


def json_not_empty(source, json_path_expr=None):
    """Check if a JSON object is not empty.
    will be used to extract JSON from candidate.
    :param json_path_expr: A optional jsonpath expression
    :param source: target to extract
    :return: `True` if the result JSON is not `{}` or `[]` or `None`
    """
    return not json_empty(source, json_path_expr)


def set_var(value):
    """Set a variable which name should be specified in `output` with value"""
    return value


_EXT_FUNCTIONS = {
    'regex_match': regex_match,
    'regex_not_match': regex_not_match,
    'set_var': set_var,
    'splunk_xml': splunk_xml,
    'std_output': std_output,
    'json_path': json_path,
    'json_empty': json_empty,
    'json_not_empty': json_not_empty,
}


def lookup_method(name):
    """ Find a predefined function with given function name.
    :param name: function name.
    :return: A function with given name.
    """
    return _EXT_FUNCTIONS.get(name)
