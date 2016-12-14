import json
import re
import logging
from ..common import util
from ..common.splunk_util import std_out


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


def json_path(expr, candidate):
    """
    Extract value from string and jsonpath expression with jsonpath.
    :param expr: jsonpath expression
    :param candidate: string to extract value
    :return: A `list` contains all values extracted
    """
    if not isinstance(candidate, dict):
        if not isinstance(candidate, basestring):
            raise TypeError('candidate expected to be dict or JSON string')
        candidate = json.loads(candidate)

    from jsonpath_rw import parse
    jsonpath_expr = parse(expr)
    results = [match.value for match in jsonpath_expr.find(candidate)]
    return results[0] if len(results) == 1 else results


def splunk_xml(candidates, time=None, index=None, host=None, source=None,
               sourcetype=None):
    """
    Wrap a event with splunk xml format.
    :return: A wrapped event with splunk xml format.
    """
    if not isinstance(candidates, (list, tuple)):
        candidates = [candidates]
    return util.format_events(candidates, time=time, index=index, host=host,
                              source=source, sourcetype=sourcetype)


def std_output(candidates):
    """
    Output a string to stdout.
    :param candidates: List of string to output to stdout or a single string.
    """
    if isinstance(candidates, basestring):
        candidates = [candidates]
    for candidate in candidates:
        if not isinstance(candidate, basestring):
            logging.warning("The type of data needs to print is {} rather"
                         "basestring".format(type(candidate)))
        std_out(candidate)


def json_empty(candidate, json_path_expr=None):
    """
    Check whether a JSON is empty.
    :param json_path_expr: A optional jsonpath expression
    :param candidate: target to extract
    :return: `True` if the result JSON is `{}` or `[]` or `None`
    """
    if json_path_expr:
        candidate = json_path(json_path_expr, candidate)
    if not candidate:
        return True
    if isinstance(candidate, (dict, list, tuple)):
        return len(candidate) == 0
    if not isinstance(candidate, basestring):
        raise TypeError('unexpected candidate %s' % str(candidate))
    return len(json.loads(candidate)) == 0


def json_not_empty(candidate, json_path_expr=None):
    """Check if a JSON object is not empty. A optional jsonpath expression
    will be used to extract JSON from candidate.
    :param json_path_expr: A optional jsonpath expression
    :param candidate: target to extract
    :return: `True` if the result JSON is not `{}` or `[]` or `None`
    """
    return not json_empty(candidate, json_path_expr)


_EXT_FUNCTIONS = {
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
