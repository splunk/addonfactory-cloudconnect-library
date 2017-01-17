from cloudconnectlib.core.ext import (
    lookup_method,
    regex_match,
    regex_not_match,
    std_output,
    splunk_xml,
    json_path,
    json_empty,
    json_not_empty,
    set_var,
    time_str2str,
)


def test_regex_match():
    assert regex_match('^From', 'From Here to Eternity')
    assert regex_match('^[A-Za-z0-9]+', '123456abcdefg')
    assert regex_match('^$', '')
    assert regex_match('', 'abcd')


def test_regex_not_match():
    assert regex_not_match('\bclass\b', 'no class at all')
    assert regex_not_match('^[A-Z]+', '123456')


def test_splunk_xml():
    event1 = splunk_xml('data1', time='', index='', source='', sourcetype='', host='')
    assert event1[0] == '<stream><event>' \
                        '<data>data1</data></event></stream>'
    event2 = splunk_xml('data2', time=12345677, index='index_test',
                        source='source_test', sourcetype='sourcetype_test',
                        host='localhost')
    assert event2[0] == '<stream><event><time>12345677.000</time><index>index_test' \
                        '</index><host>localhost</host><source>source_test' \
                        '</source><sourcetype>' \
                        'sourcetype_test</sourcetype>' \
                        '<data>data2</data></event></stream>'


def test_json_path():
    test_cases = [
        (
            {'foo': [{'baz': 1}, {'baz': 2}]},
            'foo[*].baz',
            2,
            [1, 2]
        ),
        (
            '{"foo": [{"baz": 1}, {"baz": 2}]}',
            'foo[*].baz',
            2,
            [1, 2]
        ),
        (
            [{'baz': 1}, {'baz': 2}],
            '[*].baz',
            2,
            [1, 2]
        ),
        (
            {'a': {'x': {'b': 1, 'c': 'number one'}, 'y': {'b': 2, 'c': 'number two'}}},
            'a.*.b.`parent`.c',
            2,
            ['number two', 'number one']
        ),
        (
            'abcedfghijkl$%^&#@$',
            '$',
            19,
            'abcedfghijkl$%^&#@$',
        )
    ]

    for source, expr, result_size, result in test_cases:
        r = json_path(source, expr)
        assert len(r) == result_size
        assert r == result


def test_std_output():
    import sys

    class MockStdout(object):
        def __init__(self):
            self._buf = ''
            self._size = 0

        def read(self, size=None):
            content = self._buf
            self._buf = ''
            return content

        def size(self):
            return self._size

        def write(self, event):
            self._buf += event

        def flush(self):
            self._size += len(self._buf)

    sysstdout = sys.stdout
    mock_stdout = MockStdout()
    sys.stdout = mock_stdout

    std_output('abcdefghijkl1234!@#$%^')
    sys.stdout = sysstdout

    assert mock_stdout.read() == 'abcdefghijkl1234!@#$%^\n'


def test_json_empty():
    empty_cases = ['{}', {}, '[]', [], '', ['', '', {}]]
    for case in empty_cases:
        assert json_empty(case)
        assert json_empty(case, '$')
        assert not json_not_empty(case, '$')

    not_empty_cases = [
        '{"k": 1}',
        {'k': True},
        '{"k": true}',
        '{"k": 123.456}',
    ]

    for case in not_empty_cases:
        assert json_not_empty(case)
        assert not json_empty(case)
        assert not json_empty(case, '$')
        assert not json_empty(case, '')
        assert not json_empty(case, None)
        assert not json_empty(case, '$.k')
        assert not json_not_empty(case, '$.k')

    invalid_cases = ['$$!@#', 'hahahha   ksk32', '{{}}}', '=---==', '\\=---']
    for case in invalid_cases:
        assert not json_empty(case)
        assert not json_not_empty(case)


def test_lookup():
    f = lookup_method('json_path')
    assert f == json_path
    f = lookup_method('json_not_empty')
    assert f == json_not_empty
    f = lookup_method('json_empty')
    assert f == json_empty
    f = lookup_method('set_var')
    assert f == set_var


def test_set_var():
    x1 = {'key': True}
    assert set_var(x1) == x1
    x2 = [1, 2, 3]
    assert set_var(x2) == x2
    assert set_var(True) == True
    assert set_var(False) == False
    assert set_var(1) == 1
    assert set_var(None) is None


def test_time_str2str():
    non_string = [{}, 123, [], ()]
    format1 = '%Y-%m-%d %H:%M:%S'
    format2 = '%Y-%m-%dT%H:%M:%S'

    for ns in non_string:
        r = time_str2str(ns, format1, format2)
        assert r == ns

    bad_string = ['12345', '----', '===', '$%^^&', '!@#$%^', '999999999', '-1']
    for ns in bad_string:
        r = time_str2str(ns, format1, format2)
        assert r == ns

    valid_string = [
        '2015-01-12 00:00:01',
        '2014-02-12 00:00:02',
        '2016-03-12 00:10:01',
        '2017-04-12 00:10:02',
        '2018-05-12 10:00:01',
        '2018-05-12 10:00:02',
    ]
    for ns in valid_string:
        r = time_str2str(ns, format1, format2)
        assert r == ns.replace(' ', 'T')

    format3 = '%d/%m/%y %H:%M'
    valid_string = [
        ('21/11/06 16:30', '2006-11-21T16:30:00'),
        ('10/11/06 02:30', '2006-11-10T02:30:00'),
        ('22/11/06 00:30', '2006-11-22T00:30:00'),
        ('23/11/06 01:30', '2006-11-23T01:30:00'),
    ]
    for vs, vr in valid_string:
        r = time_str2str(vs, format3, format2)

        assert r == vr
