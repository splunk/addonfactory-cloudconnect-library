from cloudconnectlib.core.model.config import CloudConnectConfig
from cloudconnectlib.core.model.global_settings import *
from cloudconnectlib.core.model.request import *
from cloudconnectlib.core.model.meta import *
from cloudconnectlib.core.client import CloudConnectClient

logging = Logging(level="INFO")

global_settings = GlobalSetting(logging=logging)
meta = Meta({"version":"1.0.0"})
config = CloudConnectConfig(meta, global_settings)
header = Header()
header.add("accept", "application/json")
url = "https://{{host}}/api/now/table/{{table_name}}?sysparm_limit={{sysparm_limit}}&sysparm_query=sys_updated_on>{{since_when}}^ORDERBYsys_updated_on"
method = "GET"
auth = BasicAuthorization(
    {"username": "{{username}}", "password": "{{password}}"})

options = Options(url, header=header, method=method, auth=auth)

skip_after_request = SkipAfterRequest()
skip_after_request_condition = Condition([
    "$.result[*]",
    "{{__response__.body}}"
], "json_empty")
skip_after_request.add_condition(skip_after_request_condition)

after_request1 = AfterRequest([
    "$.result[-1].sys_updated_on",
    "{{__response__.body}}"
], "jsonpath", "since_when")

loop_mode = LoopMode(type="loop", conditions=[skip_after_request_condition])

checkpoint = Checkpoint({
    "since_when": "{{since_when}}"
}, keys=None)

request = Request(options, [], skip_after_request,
                  [after_request1], loop_mode, checkpoint)
config.add_request(request)


context={}
context["host"] = "ven01034.service-now.com"
context["table_name"] = "incident"
context["sysparm_limit"] = "100"
context["since_when"] = "2016-11-01+12:42:23"
context["username"] = "splunk"
context["password"] = "Splunk123$"
client = CloudConnectClient(context, config)
client.run()


