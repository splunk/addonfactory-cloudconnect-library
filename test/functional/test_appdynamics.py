import pytest
from cloudconnectlib.core.task import CCEHTTPRequestTask, CCESplitTask
from cloudconnectlib.core.job import CCEJob
from cloudconnectlib.core.engine_v2 import CloudConnectEngine


def appd_application_task():
    task = CCEHTTPRequestTask(
        request={
            "url": "{{appd_host}}/controller/rest/applications?output=JSON",
            "method": "GET",
        },
        name='AppdApplicationsTask'
    )
    task.set_auth('basic_auth', {"username": "{{account.username}}",
                                 "password": "{{account.password}}"})

    task.add_postprocess_handler('json_path', ['{{__response__.body}}', "$"],
                                 'applications')
    task.add_postprocess_handler('json_path', ['{{__response__.body}}',
                                               "[*].name"],
                                 'apps')
    task.add_postprocess_handler('std_output', ['{{applications}}'], "")

    task.set_iteration_count(1)
    return task


def appd_metric_task():
    task = CCEHTTPRequestTask(
        request={
            "url": "{{appd_host}}/controller/rest/applications/{{app}}"
                   "/metric-data?output=JSON&time-range-type=BEFORE_NOW"
                   "&duration-in-mins=10"
                   "&metric-path=Overall Application Performance|*",
            "method": "GET",
        },
        name='AppdMetricTask'
    )

    task.set_auth('basic_auth', {"username": "{{account.username}}",
                                 "password": "{{account.password}}"})

    task.add_postprocess_handler('json_path', ['{{__response__.body}}', "$"],
                                 'all_res')
    task.add_postprocess_handler('std_output', ['{{all_res}}'], "")
    task.set_iteration_count(1)
    return task


def split_task():
    split_task = CCESplitTask("AppdSplitTask")
    split_task.configure_split("split_by", "{{apps}}", "app")
    return split_task


def test_appd_applications():
    account = {"username": "ChinaPowerUp@ChinaPowerUp", "password": "123456"}
    context = {"appd_host": "https://chinapowerup.saas.appdynamics.com",
               "account": account}
    job = CCEJob(context=context)
    job.add_task(appd_application_task())
    engine = CloudConnectEngine()
    engine.start([job])
    assert context["apps"] == "SampleApp"


def test_appd_metrics():
    account = {"username": "ChinaPowerUp@ChinaPowerUp", "password": "123456"}
    context = {"appd_host": "https://chinapowerup.saas.appdynamics.com",
               "app": "SampleApp", "account": account}
    job = CCEJob(context=context)
    job.add_task(appd_metric_task())
    engine = CloudConnectEngine()
    engine.start([job])
    assert len(context["all_res"]) > 1


def test_appd_dual_step():
    account = {"username": "jing@anonymaous", "password": "111111"}
    context = {"appd_host": "https://anonymaous.saas.appdynamics.com",
               "account": account}
    job = CCEJob(context=context)
    job.add_task(appd_application_task())
    job.add_task(split_task())
    job.add_task(appd_metric_task())
    engine = CloudConnectEngine()
    engine.start([job])
    assert len(context["apps"]) > 1


if __name__ == "__main__":
    test_appd_applications()
    test_appd_metrics()
    print "======= dual step start ======"
    test_appd_dual_step()
    print "======= dual step end ======"
