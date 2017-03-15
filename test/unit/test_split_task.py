import pytest
from cloudconnectlib.core.task import CCESplitTask
from cloudconnectlib.core.exceptions import CCESplitError

context = {"apps": ["app1", "app2", "app3"]}


def test_split_task_for_list():
    splittask = CCESplitTask("test_split_task_for_list")
    context = {"apps": ["app1", "app2", "app3"]}
    splittask.configure_split("split_by", "{{apps}}", "app")
    results = splittask.perform(context)
    results = list(results)
    assert len(results) == 3
    assert results[0]["app"] is not None


def test_split_task_for_empty_list():
    splittask = CCESplitTask("test_split_task_for_list")
    context = {"apps": []}
    splittask.configure_split("split_by", "{{apps}}", "app")
    results = splittask.perform(context)
    with pytest.raises(CCESplitError):
        results = list(results)

    context = {"apps_2": ["app1", "app2", "app3"]}
    results = splittask.perform(context)
    with pytest.raises(CCESplitError):
        results = list(results)


def test_split_task_for_string():
    splittask = CCESplitTask("test_split_task_for_list")
    splittask.configure_split("split_by", "{{apps}}", "app", ",")
    context = {"apps": "app1, app2, app3"}
    results = splittask.perform(context)
    results = list(results)
    assert len(results) == 3
    assert results[0]["app"] is not None

    context = {"apps": "app1"}
    results = splittask.perform(context)
    results = list(results)
    assert len(results) == 1
    assert results[0]["app"] is not None


def test_split_task_for_empty_string():
    splittask = CCESplitTask("test_split_task_for_list")
    splittask.configure_split("split_by", "{{apps}}", "app", ",")
    context = {"apps": ""}
    results = splittask.perform(context)
    with pytest.raises(CCESplitError):
        results = list(results)
