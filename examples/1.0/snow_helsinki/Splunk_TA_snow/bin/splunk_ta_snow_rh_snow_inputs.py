import os
import re

ta_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ta_lib_name = re.sub("[^\w]+", "_", ta_name.lower())
__import__(ta_lib_name + "_import_declare")
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    DataInputModel,
)
from splunktaucclib.rest_handler import admin_external
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler


fields = [
    field.RestField(
        "account", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "interval", required=False, encrypted=False, default="60", validator=None
    ),
    field.RestField(
        "snow_host", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "sysparm_limit", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "since_when", required=False, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "table_name", required=False, encrypted=False, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = DataInputModel(
    "snow_inputs",
    model,
)


if __name__ == "__main__":
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
