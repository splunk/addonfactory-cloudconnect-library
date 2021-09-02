#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from builtins import range
from builtins import object
import pytest
from cloudconnectlib.core.exceptions import StopCCEIteration
from cloudconnectlib.core.ext import (
    assert_true,
    exit_if_true,
    is_true,
    lookup_method,
    regex_match,
    regex_search,
    std_output,
    splunk_xml,
    json_path,
    json_empty,
    json_not_empty,
    set_var,
    time_str2str,
    _fix_timestamp_format,
    _fix_microsecond_format,
)


def test_regex_match():
    assert regex_match('^From', 'From Here to Eternity')
    assert regex_match('^[A-Za-z0-9]+', '123456abcdefg')
    assert regex_match('^$', '')
    assert regex_match('', 'abcd')


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
            ['number one', 'number two']
        ),
        (
            'abcedfghijkl$%^&#@$',
            '$',
            19,
            'abcedfghijkl$%^&#@$',
        ),
        (
            {'a': {'x': 'b'}},
            '$.b',
            0,
            ''
        ),
        (
            {'a': {'x': 'b'}},
            '$.a',
            1,
            {'x': 'b'}
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

    # timezone is not supported
    r = time_str2str('Tue Jun 22 12:10:20 2010 EST', '%a %b %d %H:%M:%S %Y %Z', '%Y-%m-%d %H:%M:%S %Z')
    assert r == 'Tue Jun 22 12:10:20 2010 EST'

    r = time_str2str('Tue Jun 22 12:10:20 2010 UTC', '%a %b %d %H:%M:%S %Y %Z', '%Y-%m-%d %H:%M:%S %Z')
    assert r == '2010-06-22 12:10:20 '

    # convert to timestamp
    timestamp_cases = [
        ('21/11/06 16:30', '1164126600'),
        ('10/11/06 02:30', '1163125800'),
        ('22/11/06 00:30', '1164155400'),
        ('23/11/06 01:30', '1164245400'),
    ]
    for vs, vt in timestamp_cases:
        r = time_str2str(vs, format3, '%s')
        assert r == vt


def test_fix_timestamp_format():
    cases = [
        ('%s', '1392134402', '1392134402'),
        ('%s%s%s%s', '1392134402', '1392134402139213440213921344021392134402'),
        ('abcdedfsdfg%sedfhitop', '1392134402', 'abcdedfsdfg1392134402edfhitop'),
        ('abcd%s%s%%%%%%s', '1392134402', 'abcd13921344021392134402%%%%%%s'),
        ('%%%%%s', '1392134402', '%%%%1392134402'),
        ('%%s%%s%%s%%%s', '1392134402', '%%s%%s%%s%%1392134402'),
        ('-==1234%s%S%s%SSSSss', '1392134402', '-==12341392134402%S1392134402%SSSSss')
    ]
    for fmt, tmp, result in cases:
        converted = _fix_timestamp_format(fmt, tmp)
        assert converted == result


def test_fix_microsecond_format():
    cases = [
        ('%f', '123456', '%f'),
        ('%1f %2f %3f %4f %5f %6f', '123456', '1 12 123 1234 12345 123456'),
        ('%1f %2f %3f %4f %5f %6ff', '123456', '1 12 123 1234 12345 123456f'),
        ('%7f', '123456', '%7f'),
        ('%xf', '123456', '%xf'),
        ('%%1f', '123456', '%%1f'),
        ('%%1f%%%2f', '123456', '%%1f%%12'),
        ('xx%6fxx', '1234', 'xx001234xx'),
        ('1234', '5555', '1234'),
        ('.%2f+08:00', '10000', '.01+08:00')
    ]
    for fmt, tmp, result in cases:
        converted = _fix_microsecond_format(fmt, tmp)
        assert converted == result


def _get_all_trues():
    for x in range(1 << 4):
        text = ['t', 'r', 'u', 'e']
        for j in range(4):
            if j & x:
                text[j] = text[j].upper()
        yield ''.join(text)


def test_exit_if_true():
    non_truth = [123, '123', 'not-true', '', None, [], [1, 2, 3],
                 (), (1, 2, 3), {}, {'v': True}]
    for case in non_truth:
        exit_if_true(case)

    for t in _get_all_trues():
        with pytest.raises(StopCCEIteration):
            exit_if_true(t)


def test_assert_true():
    not_truth = [123, -123, 1.2345, -1.2345, [1], (1,), {'v': 1}, 'non-empty-string']
    for nt in not_truth:
        with pytest.raises(AssertionError):
            assert_true(nt, 'value %s is not true' % nt)

    for t in _get_all_trues():
        assert_true(t, '%s is true' % t)


def test_is_true():
    for t in _get_all_trues():
        assert is_true(t)

    not_truth = [123, -123, 1.2345, -1.2345, [1], (1,), {'v': 1}, 'non-empty-string']

    for nt in not_truth:
        assert not is_true(nt)


def test_regex_search():
    source = 'absbssd234455 222'
    regex = 'ssd(?P<title>\d+)\s(?P<title2>\d+)'
    s = regex_search(regex, source)
    assert len(s) == 2
    assert s['title'] == '234455'
    assert s['title2'] == '222'

    not_matched_regex = 'ssdddddddddd----'
    s = regex_search(not_matched_regex, source)
    assert len(s) == 0

    non_string = ({}, [], (), 123, 123.4)

    assert all(len(regex_search(regex, x)) == 0 for x in non_string)
