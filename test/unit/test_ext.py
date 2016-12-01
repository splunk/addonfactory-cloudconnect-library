import os.path as op
import sys

sys.path.insert(0, op.join(op.dirname(op.dirname(op.dirname(__file__))),
                           'package', 'cloudconnectlib'))

from core.ext import (
    lookup, jsonpath, regex_match, regex_not_match, std_output,
    splunk_xml
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
    assert event1 == '<stream><event><host></host><source></source><sourcetype></sourcetype>' \
                     '<time></time><index></index><data><![CDATA[data1]]></data></event></stream>'
    event2 = splunk_xml('data2', time=12345677, index='index_test',
                        source='source_test', sourcetype='sourcetype_test',
                        host='localhost')
    assert event2 == '<stream><event><host>localhost</host><source>source_test</source><sourcetype>' \
                     'sourcetype_test</sourcetype><time>12345677</time><index>index_test</index>' \
                     '<data><![CDATA[data2]]></data></event></stream>'


def test_jsonpath():
    r = jsonpath('foo[*].baz', {'foo': [{'baz': 1}, {'baz': 2}]})
    assert r[0] == 1
    assert r[1] == 2
    rr = jsonpath('a.*.b.`parent`.c', {'a': {'x': {'b': 1, 'c': 'number one'}, 'y': {'b': 2, 'c': 'number two'}}})
    assert rr[0] == 'number two'
    assert rr[1] == 'number one'


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

    assert mock_stdout.read() == 'abcdefghijkl1234!@#$%^'
    assert mock_stdout.size() == 22


def test_lookup():
    f = lookup('jsonpath')
    r = f('foo[*].baz', {'foo': [{'baz': 1}, {'baz': 2}]})
    assert r[0] == 1
    assert r[1] == 2
