import json
import re
import sys


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


def splunk_xml(candidate, time='', index='', host='', source='', sourcetype=''):
    """
    Wrap a event with splunk xml format.
    :return: A wrapped event with splunk xml format.
    """
    return ("<stream><event><host>{host}</host>"
            "<source>{source}</source>"
            "<sourcetype>{sourcetype}</sourcetype>"
            "<time>{time}</time>"
            "<index>{index}</index><data>"
            "<![CDATA[{data}]]></data></event></stream>") \
        .format(host=host or '', source=source or '',
                sourcetype=sourcetype or '',
                time=time or '', index=index or '', data=candidate or '')


def std_output(candidate):
    """
    Output a string to stdout.
    :param candidate: string to output to stdout.
    """
    sys.stdout.write(candidate)
    sys.stdout.flush()


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


_EXT_FUNCTIONS = {
    'regex_match': regex_match,
    'regex_not_match': regex_not_match,
    'splunk_xml': splunk_xml,
    'std_output': std_output,
    'json_path': json_path,
    'json_empty': json_empty,
}


def lookup(name):
    """
    Find a predefined function with given function name.
    :param name: function name.
    :return: A function with given name.
    """
    return _EXT_FUNCTIONS.get(name)
