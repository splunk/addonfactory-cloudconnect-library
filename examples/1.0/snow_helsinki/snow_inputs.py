#!/usr/bin/python
"""
This is the main entry point for My TA
"""
import re
import os.path as op
import os

ta_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ta_lib_name = re.sub("[^\w]+", "_", ta_name.lower())
__import__(ta_lib_name + "_import_declare")

import cloudconnectlib.splunktacollectorlib.data_collection.ta_mod_input as ta_input
from cloudconnectlib.splunktacollectorlib.ta_cloud_connect_client import \
    TACloudConnectClient as collector_cls


def ta_run():
    script_name = os.path.basename(__file__).rstrip(".py")
    cc_json_file = os.path.sep.join([os.path.dirname(os.path.abspath(__file__)),
                    ".".join([script_name,"cc.json"])])
    schema_file_path = op.join(
        op.dirname(op.abspath(__file__)),
        "globalConfig.json")
    ta_input.main(collector_cls, schema_file_path, script_name,
                  cc_json_file=cc_json_file, schema_para_list=(
        "account",
        "interval", "snow_host",
        "sysparm_limit", "since_when",
        "table_name"
    ), single_instance=False)

if __name__ == "__main__":
    import sys
    #old_stdin = sys.stdin  # save it, in case we need to restore it
    #sys.stdin = sys.stdin = open('input.xml')
    ta_run()
