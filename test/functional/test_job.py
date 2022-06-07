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
import json
import logging
import os.path as op
import sys

from cloudconnectlib.common.log import set_cc_logger
from cloudconnectlib.core.job import CCEJob
from cloudconnectlib.core.task import CCEHTTPRequestTask

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
root.addHandler(ch)

set_cc_logger(root, "")

context = {
    "host": "ven01034.service-now.com",
    "table_name": "incident",
    "sysparm_limit": 100,
    "since_when": "2016-11-01 12:42:23",
    "username": "splunk",
    "password": "Splunk123$",
}


def _get_proxy_config():
    fp = op.join(op.dirname(__file__), "proxy.json")
    with open(fp, "r") as jfp:
        return json.load(jfp)


if __name__ == "__main__":

    context.update(_get_proxy_config())

    job = CCEJob(context=context)

    task = CCEHTTPRequestTask(
        request={
            "url": "https://httpbin.org/get",
            "method": "GET",
        },
        name="HttpTask",
    )

    task.set_proxy(
        proxy_setting={
            "proxy_enabled": True,
            "proxy_type": "{{proxy_type}}",
            "proxy_url": "{{proxy_url}}",
            "proxy_port": "{{proxy_port}}",
            "proxy_username": "{{proxy_username}}",
            "proxy_password": "{{proxy_password}}",
            "proxy_rdns": "{{proxy_rdns}}",
        }
    )

    task.add_postprocess_handler("json_path", ["{{__response__.body}}", "$"], "all_res")
    task.add_postprocess_handler("std_output", ["{{all_res}}"], "")
    task.set_iteration_count(1)

    job.add_task(task)

    print("run job")

    for x in job.run():
        pass

    print("finished job")
