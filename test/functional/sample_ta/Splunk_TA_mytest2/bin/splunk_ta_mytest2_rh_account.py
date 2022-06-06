import splunk_ta_mytest2_import_declare

from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external, util
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler

util.remove_http_proxy_env_vars()


fields = [
    field.RestField(
        "server_url",
        required=True,
        encrypted=False,
        default="https://app-builder.sv.splunk.com/rest/api/latest/project.json",
        validator=None,
    ),
    field.RestField(
        "username",
        required=True,
        encrypted=False,
        default=None,
        validator=validator.Pattern(
            regex=r"""\w{1,50}""",
        ),
    ),
    field.RestField(
        "password", required=True, encrypted=True, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "splunk_ta_mytest2_account",
    model,
)


if __name__ == "__main__":
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
