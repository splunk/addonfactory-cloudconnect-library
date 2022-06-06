import splunk_ta_mysolarwinds_import_declare

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
        "account", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "interval", required=False, encrypted=False, default="60", validator=None
    ),
    field.RestField(
        "eventtime", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "index", required=True, encrypted=False, default="default", validator=None
    ),
    field.RestField("disabled", required=False, validator=None),
]
model = RestModel(fields, name=None)


endpoint = DataInputModel(
    "solarwind_input",
    model,
)


if __name__ == "__main__":
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
