import os
import os.path as op
from .data_collection import ta_mod_input as ta_input
from .ta_cloud_connect_client import TACloudConnectClient as collector_cls
from .mod_helper import get_main_file


def run(schema_para_list=None, single_instance=False):
    script_name = os.path.basename(get_main_file()).rstrip(".py")
    cc_json_file = os.path.sep.join(
        [os.path.dirname(os.path.abspath(get_main_file())),
                                     ".".join([script_name, "cc.json"])])
    schema_file_path = op.join(
        op.dirname(op.abspath(get_main_file())),
        "globalConfig.json")
    ta_input.main(collector_cls, schema_file_path, script_name,
                  cc_json_file=cc_json_file, schema_para_list=schema_para_list,
                  single_instance=single_instance)
