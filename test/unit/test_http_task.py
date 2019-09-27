from __future__ import absolute_import
import six
from builtins import object
import os
import sys

from . import common

sys.path.append(os.path.join(common.PROJECT_ROOT, "package"))

from cloudconnectlib.core.task import CCEHTTPRequestTask


class MockedHttpResponse(object):
    def __init__(self, url):
        self.url = url

    @property
    def header(self):
        args = self.url.split('&')
        if args and args[-1].startswith("page="):
            n = args[-1].split('=')[1]
            url = self.url[0:-1] + '%s' % (int(n) + 1)
        else:
            url = self.url + "&page=2"
        return {
            'link': url
        }

    @property
    def body(self):
        return """{
  "items": [
    {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
      "Accept-Encoding": "gzip, deflate, sdch, br"
    },
    {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
      "Accept-Encoding": "gzip, deflate, sdch, br"
    }
  ]
}"""

    @property
    def status_code(self):
        return 200


def mock_send_request(self, client, request):
    return MockedHttpResponse(request.url), False


def generate_task(monkeypatch, pagination=True):
    if pagination:
        task = CCEHTTPRequestTask(
            request={
                "url": "https://api.github.com/search/code?q=addClass+user%3Amozilla",
                "method": "GET",
                "nextpage_url": "{{__nextpage_url__}}"
            },
            name='test_github'
        )
    else:
        task = CCEHTTPRequestTask(
            request={
                "url": "https://api.github.com/search/code?q=addClass+user:mozilla",
                "method": "GET"
            },
            name='test_github'
        )
    monkeypatch.setattr(CCEHTTPRequestTask, '_send_request', mock_send_request)

    task.add_postprocess_handler(method='set_var',
                                 input=["{{__response__.header.link}}"],
                                 output='__nextpage_url__')
    task.add_postprocess_handler(method='json_path',
                                 input=["{{__response__.body}}",
                                        "$.items[*]"],
                                 output="__stdout__")
    return task


def test_original_func(monkeypatch):
    task = generate_task(monkeypatch, pagination=False)
    context = {}
    task.set_iteration_count(1)
    for x in task.perform(context):
        pass


def test_nextpage_url(monkeypatch):
    task = generate_task(monkeypatch, pagination=True)
    context = {}
    task.set_iteration_count(1)

    for x in task.perform(context):
        pass
    assert isinstance(context.get("__stdout__"), list) and \
           len(context.get("__stdout__")) > 0
    assert isinstance(context.get("__nextpage_url__"), six.string_types)
    assert context["__nextpage_url__"] == \
           "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=2"
    assert task._request.count == 1

    task = generate_task(monkeypatch)
    context = {}
    task.set_iteration_count(2)
    for x in task.perform(context):
        pass
    assert task._request.count == 2
    assert context["__nextpage_url__"] == \
           "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=3"

    task = generate_task(monkeypatch)
    context = {}
    task.set_iteration_count(3)
    for x in task.perform(context):
        pass
    assert isinstance(context.get("__stdout__"), list) and len(context.get("__stdout__")) > 0
    assert context["__nextpage_url__"] == \
           "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=4"

    context = {}
    task.set_iteration_count(3)
    task._finished_iter_count = 0
    for x in task.perform(context):
        pass
    assert isinstance(context.get("__stdout__"), list) and len(context.get("__stdout__")) > 0
    assert context["__nextpage_url__"] == \
           "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=4"
