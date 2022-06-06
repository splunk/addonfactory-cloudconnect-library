import splunk_ta_mytest_kvstore_import_declare

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "account", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "interval", required=True, encrypted=False, default="60", validator=None
    ),
    field.RestField(
        "limit_count", required=True, encrypted=False, default="3", validator=None
    ),
    field.RestField(
        "event_id",
        required=True,
        encrypted=False,
        default="tev68-uivCfTyCY61j_ynLDdQ1305564165000",
        validator=None,
    ),
    field.RestField(
        "index", required=True, encrypted=False, default="default", validator=None
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)


endpoint = DataInputModel(
    "inputs_okta_kv_1",
    model,
)


if __name__ == "__main__":
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
