#
# Copyright 2024 Splunk Inc.
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
from cloudconnectlib.core.http import _make_prepare_url_func


def test_make_prepare_url_func():
    prepare_func = _make_prepare_url_func()
    url1 = "https://jira.splunk.com/browse/ADDON+12156"

    rurl1 = prepare_func(url1)
    assert rurl1 == "https://jira.splunk.com/browse/ADDON+12156"

    url2 = "https://jira.splunk.com/browse/abc%26xyz%3D123"
    rurl2 = prepare_func(url2)

    assert rurl2 == url2

    url3 = "https://jira.splunk.com/browse/ADDON 12156"
    rurl3 = prepare_func(url3)

    assert rurl3 == "https://jira.splunk.com/browse/ADDON%2012156"

    url4 = "https://jira.splunk.com/browse/ADDONS?number=ADDON%2012156&view_type=detail"
    rurl4 = prepare_func(url4)

    assert rurl4 == url4

    url5 = "https://jira.splunk.com/browse/Query?JIRA=ADDON+12256"
    rurl5 = prepare_func(url5)
    assert rurl5 == url5

    url6 = "https://jira.splunk.com/browse/Query?JIRA_NUMBER=abc%26xyz%3D123"
    rurl6 = prepare_func(url6)
    assert url6 == rurl6

    url7 = "https://jira.splunk.com/browse/Query?JIRA=ADDON 12156"
    url8 = "https://jira.splunk.com/browse/Query?JIRA=abc&xyz=123"
    url9 = "https://jira.splunk.com/browse/Query?JIRA=ADDON=123"

    rurl7 = prepare_func(url7)
    rurl8 = prepare_func(url8)
    rurl9 = prepare_func(url9)

    assert rurl7 == "https://jira.splunk.com/browse/Query?JIRA=ADDON%2012156"
    assert rurl8 == url8
    assert rurl9 == url9
