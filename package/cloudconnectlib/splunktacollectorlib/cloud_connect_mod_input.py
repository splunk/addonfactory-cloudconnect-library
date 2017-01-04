import ConfigParser
import os
import os.path as op

from .data_collection import ta_mod_input as ta_input
from .ta_cloud_connect_client import TACloudConnectClient as CollectorCls
from ..common.lib_util import get_main_file


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


def _find_ucc_global_config_json(mod_input_abspath, ucc_config_filename):
    """Find UCC config file from all possible directories"""
    candidates = ['local', 'default', 'bin',
                  op.join('appserver', 'static', 'js', 'build')]
    app_root = op.dirname(op.dirname(mod_input_abspath))

    for candidate in candidates:
        file_path = op.join(app_root, candidate, ucc_config_filename)
        if op.isfile(file_path):
            return file_path
    raise RuntimeError(
        'Unable to load %s from [%s]'
        % (ucc_config_filename, ','.join(candidates))
    )


def _get_cloud_connect_config_json(mod_input_abspath, script_name):
    config_file_name = '.'.join([script_name, 'cc.json'])
    return op.join(op.dirname(mod_input_abspath), config_file_name)


def run(single_instance=False):
    mod_input_file = get_main_file()

    script_name = os.path.basename(mod_input_file)
    if script_name.lower().endswith('.py'):
        script_name = script_name[:-3]

    mod_input_abspath = op.abspath(mod_input_file)
    cc_json_file = _get_cloud_connect_config_json(
        mod_input_abspath, script_name
    )

    ucc_config_path = _find_ucc_global_config_json(
        mod_input_abspath, 'globalConfig.json'
    )

    ta_input.main(CollectorCls,
                  schema_file_path=ucc_config_path,
                  log_suffix=script_name,
                  cc_json_file=cc_json_file,
                  schema_para_list=_load_options_from_inputs_spec(script_name),
                  single_instance=single_instance)
