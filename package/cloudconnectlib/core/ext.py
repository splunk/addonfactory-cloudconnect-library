import json
import re

from jsonpath_rw import parse
from .exceptions import FuncException
from .pipemgr import PipeManager
from ..common import util, log

_logger = log.get_cc_logger()


def regex_match(pattern, candidate):
    """
    Determine a string match a regex pattern.

    :param pattern: regex expression
    :param candidate: candidate to match regex
    :return: `True` if candidate match pattern else `False`
    """
    return re.match(pattern, candidate) is not None


def regex_not_match(pattern, candidate):
    """
    Determine a string not match a regex pattern.

    :param pattern: regex expression
    :param candidate: candidate to match regex
    :return: `True` if candidate not match pattern else `False`
    """
    return not regex_match(pattern, candidate)


def json_path(json_path_expr, candidate):
    """
    Extract value from string and jsonpath expression with jsonpath.
    :param json_path_expr: jsonpath expression
    :param candidate: string to extract value
    :return: A `list` contains all values extracted
    """
    if not isinstance(candidate, dict):
        if not isinstance(candidate, basestring):
            raise TypeError('candidate expected to be dict or JSON string')
        try:
            candidate = json.loads(candidate)
        except ValueError:
            _logger.exception('Cannot load JSON from: %s', candidate)
            raise ValueError('Invalid JSON string: %s' % candidate)

    expression = parse(json_path_expr)
    results = [match.value for match in expression.find(candidate)]
    return results[0] if len(results) == 1 else results


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
            raise ValueError('"time" must be float: %s' % time)
    return util.format_events(candidates, time=time, index=index, host=host,
                              source=source, sourcetype=sourcetype)


def std_output(candidates):
    """
    Output a string to stdout.
    :param candidates: List of string to output to stdout or a single string.
    """
    if isinstance(candidates, basestring):
        candidates = [candidates]
    all_str = True
    for candidate in candidates:
        if all_str and not isinstance(candidate, basestring):
            all_str = False
            _logger.warning("The type of data needs to print is {} rather "
                            "than basestring".format(type(candidate)))
        if not PipeManager().write_events(candidate):
            raise FuncException("Fail to output data to stdout. The Event "
                                "writer has stopped or encountered exception")

    _logger.debug('Writing events to stdout finished.')
    return True


def json_empty(json_path_expr, candidate):
    """
    Check whether a JSON is empty.
    :param json_path_expr: A optional jsonpath expression
    :param candidate: target to extract
    :return: `True` if the result JSON is `{}` or `[]` or `None`
    """
    if not candidate:
        _logger.debug(
            'JSON to check is empty, treating it as empty: %s',
            candidate)
        return True

    if json_path_expr:
        candidate = json_path(json_path_expr, candidate)
    if not candidate:
        return True

    if isinstance(candidate, (dict, list, tuple)):
        return len(candidate) == 0
    if not isinstance(candidate, basestring):
        raise TypeError('unexpected candidate %s' % str(candidate))

    try:
        return len(json.loads(candidate)) == 0
    except ValueError:
        _logger.warning(
            'Cannot load JSON from string, treating is as not empty')
        return False


def json_not_empty(candidate, json_path_expr=None):
    """Check if a JSON object is not empty. A optional jsonpath expression
    will be used to extract JSON from candidate.
    :param json_path_expr: A optional jsonpath expression
    :param candidate: target to extract
    :return: `True` if the result JSON is not `{}` or `[]` or `None`
    """
    return not json_empty(candidate, json_path_expr)


def alias(value):
    """Alias a variable to another which should be
    specified in `output`"""
    return value


_EXT_FUNCTIONS = {
    'alias': alias,
    'regex_match': regex_match,
    'regex_not_match': regex_not_match,
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
