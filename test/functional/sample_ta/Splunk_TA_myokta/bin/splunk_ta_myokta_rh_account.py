
import splunk_ta_myokta_import_declare

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
        'okta_url',
        required=True,
        encrypted=False,
        default=None,
        validator=None
    ), 
    field.RestField(
        'api_key',
        required=True,
        encrypted=True,
        default=None,
        validator=None
    )
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    'splunk_ta_myokta_account',
    model,
)


if __name__ == '__main__':
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
