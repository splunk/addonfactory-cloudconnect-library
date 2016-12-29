import pytest
from cloudconnectlib.core.models import _Token, _DictToken, Request
from jinja2 import TemplateSyntaxError


def test_token_render():
    int_token = _Token(123)
    ctx = {}
    assert int_token.render(ctx) == 123

    str_token = _Token('token_without_template')
    assert str_token.render(ctx) == 'token_without_template'

    str_token_with_space = _Token('token token ')
    assert str_token_with_space.render(ctx) == 'token token '

    tokens = [
        '{{var}}',
        '{{var }}',
        '{{ var}}',
        '{{ var }}',
    ]
    for tk in tokens:
        real_token = _Token(tk)
        ctx = {'var': 123}
        assert real_token.render(ctx) == 123
        ctx = {'var': ''}
        assert real_token.render(ctx) == ''
        ctx = {'var': None}
        assert real_token.render(ctx) == ''

    bad_tokens = ['{{ abc}', '{{}}']
    for bt in bad_tokens:
        with pytest.raises(TemplateSyntaxError):
            _Token(bt)

    assert _Token('{ {abc}}').render({'abc': '123'}) == '{ {abc}}'


def test_dict_token():
    tokens_as_dict = {
        'abc': '{{xyz}}',
        'int': '{{int}}'
    }
    dt = _DictToken(tokens_as_dict)

    dtv = dt.render({'xyz': 'abc_test', 'int': 124})
    print dtv
    assert dtv['abc'] == 'abc_test'
    assert dtv['int'] == 124


def test_request():
    header = {
        'token1': 124,
        'token2': '{{value1}}'
    }
    body = {
        'params1': 123,
        'params2': '{{value2}}'
    }
    option = Request('url_test', 'GET',
                     header=header, auth=None,
                     body=body)

    htv = option.normalize_header({'value1': 'value_test'})
    assert htv['token1'] == '124'
    assert htv['token2'] == 'value_test'

    body = option.normalize_body({'value2': 'value_test'})
    assert body['params1'] == 123
    assert body['params2'] == 'value_test'
