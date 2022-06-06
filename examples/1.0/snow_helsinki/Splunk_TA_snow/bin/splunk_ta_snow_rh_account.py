import os
import re

ta_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ta_lib_name = re.sub("[^\w]+", "_", ta_name.lower())
__import__(ta_lib_name + "_import_declare")
from splunktaucclib.rest_handler.endpoint import (
    field,
    validator,
    RestModel,
    SingleModel,
)
from splunktaucclib.rest_handler import admin_external
from splunktaucclib.rest_handler.admin_external import AdminExternalHandler


fields = [
    field.RestField(
        "username", required=True, encrypted=False, default=None, validator=None
    ),
    field.RestField(
        "password", required=True, encrypted=False, default=None, validator=None
    ),
]
model = RestModel(fields, name=None)


endpoint = SingleModel(
    "splunk_ta_snow_account",
    model,
)


if __name__ == "__main__":
    admin_external.handle(
        endpoint,
        handler=AdminExternalHandler,
    )
