import ConfigParser
import os
import os.path as op

from .data_collection import ta_mod_input as ta_input
from .mod_helper import get_main_file
from .ta_cloud_connect_client import TACloudConnectClient as collector_cls


def _load_options_from_inputs_spec(stanza_name):
    root = op.dirname(op.dirname(op.abspath(get_main_file())))
    input_spec_file = 'inputs.conf.spec'
    file_path = op.join(root, 'README', input_spec_file)

    if not op.isfile(file_path):
        raise RuntimeError("README/%s doesn't exist" % input_spec_file)

    parser = ConfigParser.RawConfigParser(allow_no_value=True)
    parser.read(file_path)
    options = parser.defaults().keys()
    stanza_prefix = '%s://' % stanza_name

    stanza_exist = False
    for section in parser.sections():
        if section == stanza_name or section.startswith(stanza_prefix):
            options.extend(parser.options(section))
            stanza_exist = True
    if not stanza_exist:
        raise RuntimeError("Stanza %s doesn't exist" % stanza_name)
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
