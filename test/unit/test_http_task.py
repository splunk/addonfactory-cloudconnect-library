import pytest
import sys
import os
import common
sys.path.append(os.path.join(common.PROJECT_ROOT, "package"))


def generate_task(pagination=True):
    from cloudconnectlib.core.task import CCEHTTPRequestTask
    if pagination:
        task = CCEHTTPRequestTask(
            request={
                "url": "https://api.github.com/search/code?q=addClass+user:mozilla",
                "method": "GET",
                "nextpage_url": "{{__nextpage_url__['link']}}"
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

    task.add_postprocess_handler(method='regex_search',
                                 input=["<(?P<link>[^>]+)>;\\s*rel=.next.,",
                                        "{{__response__.header.link}}"],
                                 output='__nextpage_url__')
    task.add_postprocess_handler(method='json_path',
                                 input=["{{__response__.body}}",
                                        "$.items[*]"],
                                 output="__stdout__")
    task.add_postprocess_handler(method='std_output',
                                 input=["{{__stdout__}}"])
    task.add_stop_condition(method='regex_not_match',
                            input=[".*rel=.next.*",
                                   "{{__response__.header.link}}"])
    return task


def test_original_func(capsys):
    task = generate_task(pagination=False)
    context = {}
    task.set_iteration_count(1)
    for x in task.perform(context):
        pass


def test_nextpage_url(capsys):
    import time
    task = generate_task()
    context = {}
    task.set_iteration_count(1)
    for x in task.perform(context):
        pass
    assert isinstance(context.get("__stdout__"), list) and \
        len(context.get("__stdout__")) > 0
    assert isinstance(context.get("__nextpage_url__"), dict)
    assert context["__nextpage_url__"].get("link") == \
        "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=2"
    assert task._request.count == 1
    time.sleep(5)

    task = generate_task()
    context = {}
    task.set_iteration_count(2)
    for x in task.perform(context):
        pass
    assert task._request.count == 2
    assert context["__nextpage_url__"].get("link") == \
        "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=3"
    time.sleep(5)

    task = generate_task()
    context = {}
    task.set_iteration_count(3)
    for x in task.perform(context):
        pass
    assert isinstance(context.get("__stdout__"), list) and len(context.get("__stdout__")) > 0
    assert context["__nextpage_url__"].get("link") == "https://api.github.com/search/code?q=addClass+user%3Amozilla&page=4"
