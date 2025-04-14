#
# Copyright 2025 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import base64

import pytest
from jinja2 import TemplateSyntaxError

from cloudconnectlib.core.models import (
    BasicAuthorization,
    Condition,
    DictToken,
    RequestParams,
    _Token,
)


def test_token_render():
    int_token = _Token(123)
    ctx = {}
    assert int_token.render(ctx) == 123

    str_token = _Token("token_without_template")
    assert str_token.render(ctx) == "token_without_template"

    str_token_with_space = _Token("token token ")
    assert str_token_with_space.render(ctx) == "token token "

    tokens = [
        "{{var}}",
        "{{var }}",
        "{{ var}}",
        "{{ var }}",
    ]
    for tk in tokens:
        real_token = _Token(tk)
        ctx = {"var": 123}
        assert real_token.render(ctx) == 123
        ctx = {"var": ""}
        assert real_token.render(ctx) == ""
        ctx = {"var": None}
        assert real_token.render(ctx) == ""

    bad_tokens = ["{{ abc}", "{{}}"]
    for bt in bad_tokens:
        with pytest.raises(TemplateSyntaxError):
            _Token(bt)

    assert _Token("{ {abc}}").render({"abc": "123"}) == "{ {abc}}"


def test_dict_token():
    tokens_as_dict = {"abc": "{{xyz}}", "int": "{{int}}"}
    dt = DictToken(tokens_as_dict)

    dtv = dt.render({"xyz": "abc_test", "int": 124})
    print(dtv)
    assert dtv["abc"] == "abc_test"
    assert dtv["int"] == 124


def test_request():
    header = {"token1": 124, "token2": "{{value1}}"}
    body = {"params1": 123, "params2": "{{value2}}"}
    option = RequestParams("url_test", "GET", header=header, auth=None, body=body)

    htv = option.normalize_headers({"value1": "value_test"})
    assert htv["token1"] == "124"
    assert htv["token2"] == "value_test"

    body = option.normalize_body({"value2": "value_test"})
    assert body["params1"] == 123
    assert body["params2"] == "value_test"


def test_basic_auth():
    options = [{}, {"username": ""}, {"username": None}, {"password": ""}]
    for option in options:
        with pytest.raises(ValueError):
            BasicAuthorization(option)

    credentials = [
        {"username": "admin", "password": "abcdefg"},
        {"username": "xyz", "password": "xyz"},
    ]
    for c in credentials:
        auth = BasicAuthorization(c)
        headers = {}
        auth(headers, {})
        assert (
            headers["Authorization"]
            == "Basic %s"
            % base64.b64encode(
                f"{c['username']}:{c['password']}".encode(),
            )
            .decode("utf-8")
            .strip()
        )


def test_calculate_conditions():
    args = ["{}", "$"]
    con = Condition(inputs=args, function="json_empty")
    assert con.calculate({})

    args = ["{{abc}}", "$"]
    ctx = {"abc": "{}"}
    con = Condition(inputs=args, function="json_empty")
    assert con.calculate(ctx)

    args = ["ASDFGG!@#$%"]
    con = Condition(inputs=args, function="json_empty")
    assert not con.calculate({})
