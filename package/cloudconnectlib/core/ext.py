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
    except Exception:
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
    if not source:
        _logger.debug('source to apply JSONPATH is empty, return empty.')
        return ''

    if isinstance(source, basestring):
        _logger.debug(
            'source expected is a JSON, not %s. Attempt to'
            ' convert it to JSON',
            type(source)
        )
        try:
            source = json.loads(source)
        except Exception as ex:
            _logger.warning(
                'Unable to load JSON from source: %s.'
                'Attempt to apply JSONPATH "%s" on source directly.',
                ex.message,
                json_path_expr
            )

    try:
        expression = parse(json_path_expr)
        results = [match.value for match in expression.find(source)]

        _logger.debug(
            'Got %s elements extracted with JSONPATH expression "%s"',
            len(results), json_path_expr
        )
        return results[0] or '' if len(results) == 1 else results
    except Exception as ex:
        _logger.warning(
            'Unable to apply JSONPATH expression "%s" on source,'
            ' message=%s cause=%s',
            json_path_expr,
            ex.message,
            traceback.format_exc()
        )
    return ''


def splunk_xml(candidates,
               time=None,
               index=None,
               host=None,
               source=None,
               sourcetype=None):
    """ Wrap a event with splunk xml format.
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
            raise FuncException('Fail to output data to stdout. The event'
                                ' writer is stopped or encountered exception')

    _logger.debug('Writing events to stdout finished.')
    return True


def _parse_json(source, json_path_expr=None):
    if not source:
        _logger.debug('Unable to parse JSON from empty source, return empty.')
        return {}

    if json_path_expr:
        _logger.debug(
            'Try to extract JSON from source with JSONPATH expression: %s, ',
            json_path_expr
        )
        source = json_path(source, json_path_expr)

    return json.loads(source) if isinstance(source, basestring) else source


def json_empty(source, json_path_expr=None):
    """Check whether a JSON is empty, return True only if the JSON to
     check is a valid JSON and is empty.
    :param json_path_expr: A optional JSONPATH expression
    :param source: source to extract JSON
    :return: `True` if the result JSON is empty
    """
    try:
        data = _parse_json(source, json_path_expr)
    except Exception as ex:
        _logger.warning(
            'Unable to load JSON from source, treat it as '
            'not json_empty: %s', ex.message
        )
        return False

    if isinstance(data, (list, tuple)):
        return all(len(ele) == 0 for ele in data)
    return len(data) == 0


def json_not_empty(source, json_path_expr=None):
    """Check if a JSON object is not empty, return True only if the
     source is a valid JSON object and the value leading by
     json_path_expr is empty.
    :param json_path_expr: A optional JSONPATH expression
    :param source: source to extract JSON
    :return: `True` if the result JSON is not empty
    """
    try:
        data = _parse_json(source, json_path_expr)
    except Exception as ex:
        _logger.warning(
            'Unable to load JSON from source, treat it as not '
            'json_not_empty: %s',
            ex.message
        )
        return False

    if isinstance(data, (list, tuple)):
        return any(len(ele) > 0 for ele in data)
    return len(data) > 0


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
