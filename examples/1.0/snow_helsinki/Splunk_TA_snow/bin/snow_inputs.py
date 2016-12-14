#!/usr/bin/python
"""
This is the main entry point for My TA
"""
import re
import os

ta_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ta_lib_name = re.sub("[^\w]+", "_", ta_name.lower())
__import__(ta_lib_name + "_import_declare")

import cloudconnectlib.splunktacollectorlib.cloud_connect_mod_input as mod_input

def ta_run():
    schema_para_list = ["account", "interval", "snow_host", "sysparm_limit",
                         "since_when", "table_name"]
    mod_input.run(schema_para_list=schema_para_list)

if __name__ == "__main__":
    ta_run()
