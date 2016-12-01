import re


def regex_match(pattern, candidate):
    """
    Determine a string match a regex pattern.

    :param pattern: regex expression
    :param candidate: candidate to match regex
    :return: `True` if candidate match pattern else `False`
    """
    return re.match(pattern, candidate)


def regex_not_match(pattern, candidate):
    """
    Determine a string not match a regex pattern.

    :param pattern: regex expression
    :param candidate: candidate to match regex
    :return: `True` if candidate not match pattern else `False`
    """
    return not re.match(pattern, candidate)


def jsonpath(expr, candidate):
    """
    Extract value from string and jsonpath expression with jsonpath.
    :param expr: jsonpath expression
    :param candidate: string to extract value
    :return: A `list` contains all values extracted
    """
    from jsonpath_rw import parse
    jsonpath_expr = parse(expr)
    return [match.value for match in jsonpath_expr.find(candidate)]


def splunk_xml(candidate, time='', index='', host='', source='', sourcetype=''):
    """
    Wrap a event with splunk xml format.
    :return: A wrapped event with splunk xml format.
    """
    return ("<stream><event><host>{0}</host><source>{1}</source>"
            "<sourcetype>{2}</sourcetype>"
            "<time>{3}</time>"
            "<index>{4}</index><data>"
            "<![CDATA[{5}]]></data></event></stream>") \
        .format(host, source, sourcetype, time, index, candidate)


def std_output(string):
    """
    Output a string to stdout.
    :param string: string to output to stdout.
    """
    import sys
    sys.stdout.write(string)
    sys.stdout.flush()
