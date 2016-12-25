from cloudconnectlib.common.util import (
    is_valid_bool,
    is_true,
    is_valid_port,
)


def test_is_true():
    good_true = ['1', 'TRUE', 'T', 'Y', 'YES',
                 'True', 'TRue', 't', 'true', 'y',
                 'yes', 'Yes', 'YEs', 'yEs']
    assert all(is_true(v) for v in good_true)
    bad_true = ['N', 'no', '123', ' ', 'NOO', 'zbc']
    assert all(not is_true(v) for v in bad_true)


def test_is_valid_bool():
    good_true = ['1', 'TRUE', 'T', 'Y', 'YES',
                 'True', 'TRue', 't', 'true', 'y',
                 'yes', 'Yes', 'YEs', 'yEs']
    assert all(is_valid_bool(v) for v in good_true)

    good_false = ['0', 'FALSE', 'F', 'N', 'NO', 'NONE', '',
                  'False', 'FalSe', 'FALse', 'f', 'n', 'no', 'none']
    assert all(is_valid_bool(v) for v in good_false)

    bad_bool = ['124', '   h', 'Hello', '^', '=', '#$$',
                '--', 'asdf']
    assert all(not is_valid_bool(v) for v in bad_bool)


def test_is_valid_port():
    good_ports = ['1', 1, '2', 2, 1024, '1024', '65535', 65535]
    assert all(is_valid_port(p) for p in good_ports)
    bad_ports = [0, '0', -1, '-1', 65536, '65536',
                 '1234567', '$%^&', '==']
    assert all(not is_valid_port(p) for p in bad_ports)
