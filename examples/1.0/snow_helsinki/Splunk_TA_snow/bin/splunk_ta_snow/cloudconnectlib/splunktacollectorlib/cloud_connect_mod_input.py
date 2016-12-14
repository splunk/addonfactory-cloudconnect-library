import os
import os.path as op
from .data_collection import ta_mod_input as ta_input
from .ta_cloud_connect_client import TACloudConnectClient as collector_cls
from __main__ import __file__


def run(schema_para_list=[], single_instance=False):
    script_name = os.path.basename(__file__).rstrip(".py")
    print script_name
    cc_json_file = os.path.sep.join([os.path.dirname(os.path.abspath(__file__)),
                                     ".".join([script_name, "cc.json"])])
    schema_file_path = op.join(
        op.dirname(op.abspath(__file__)),
        "globalConfig.json")
    ta_input.main(collector_cls, schema_file_path, script_name,
                  cc_json_file=cc_json_file, schema_para_list=schema_para_list,
                  single_instance=single_instance)
