import pytest
from cloudconnectlib.core.template import compile_template
from jinja2 import TemplateSyntaxError


def test_compile_template():
    exprs = [('{{ xbc }}', ''), ('{{abx}}', 'abx_v'), ('{{ anc }}', 'anc_v')]

    ctx = {'abx': 'abx_v', 'anc': 'anc_v'}
    for ex, val in exprs:
        ct = compile_template(ex)
        assert ct(ctx) == val

    bad_exprs = ['{{}}', '{{}', '{   {{}']
    for br in bad_exprs:
        with pytest.raises(TemplateSyntaxError):
            compile_template(br)

    not_exprs = ['{}}', '{}{}', '{  {} }']
    for nr in not_exprs:
        ct = compile_template(nr)
        assert ct(ctx) == nr

    one_exprs = ['{{abc}}', '{{ abc }}']
    for expr in one_exprs:
        func = compile_template(expr)
        ctx = {'abc': 1245}
        assert func(ctx) == 1245

        ctx = {'abc': [1, 2, 3, 4]}
        assert func(ctx) == [1, 2, 3, 4]
        ctx = {'abc': '12345'}
        assert func(ctx) == '12345'

        ctx = {'abc': {'c1': 'v1'}}
        assert func(ctx) == {'c1': 'v1'}

        ctx = {'abc': ''}
        assert func(ctx) == ''

        ctx = {}
        assert func(ctx) == ''
