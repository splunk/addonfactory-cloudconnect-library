import ConfigParser
import os
import os.path as op
import re

from .common import log as stulog
from .data_collection import ta_mod_input as ta_input
from .mod_helper import get_main_file
from .ta_cloud_connect_client import TACloudConnectClient as collector_cls


def _load_options_from_inputs_spec(stanza_name):
    root = op.dirname(op.dirname(op.abspath(get_main_file())))
    input_spec_file = 'inputs.conf.spec'
    file_path = None

    for d in os.listdir(root):
        if re.match('^README$', d, re.IGNORECASE):
            file_path = op.join(root, d, input_spec_file)
            if op.isfile(file_path):
                break

    if not file_path:
        stulog.logger.warning("%s doesn't exist", input_spec_file)
        return None

    parser = ConfigParser.RawConfigParser(allow_no_value=True)
    parser.read(file_path)
    options = parser.defaults().keys()
    stanza_prefix = '%s://' % stanza_name

    for section in parser.sections():
        if section.startswith(stanza_prefix):
            options.extend(parser.options(section))
    return set(options)


def run(single_instance=False):
    script_name = os.path.basename(get_main_file()).rstrip(".py")
    cc_json_file = os.path.sep.join(
        [os.path.dirname(os.path.abspath(get_main_file())),
         ".".join([script_name, "cc.json"])])
    schema_file_path = op.join(
        op.dirname(op.abspath(get_main_file())),
        "globalConfig.json")
    ta_input.main(collector_cls, schema_file_path, script_name,
                  cc_json_file=cc_json_file,
                  schema_para_list=_load_options_from_inputs_spec(script_name),
                  single_instance=single_instance)
