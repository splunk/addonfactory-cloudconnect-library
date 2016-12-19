import socket
import ta_consts as c
import os.path as op
from ...splunktalib import splunk_cluster as sc
import ta_helper as th
from ..common import log as stulog
from ...splunktalib import modinput as modinput
from ...splunktalib.common import util


# methods can be overrided by subclass : process_task_configs
class TaConfig(object):
    _current_hostname = socket.gethostname()
    _appname = util.get_appname_from_path(op.abspath(__file__))

    def __init__(self, meta_config, client_schema, log_suffix=None,
                 stanza_name=None, input_type=None,
                 single_instance=True):
        self._meta_config = meta_config
        self._stanza_name = stanza_name
        self._input_type = input_type
        self._log_suffix = log_suffix
        self._single_instance = single_instance
        if self._stanza_name and self._log_suffix:
            stulog.reset_logger(self._log_suffix + "_" +
                                th.format_name_for_file(
                                    self._stanza_name))
            stulog.logger.info("Start {} task".format(self._stanza_name))
        self._task_configs = []
        self._client_schema = client_schema
        self._server_info = sc.ServerInfo(meta_config[c.server_uri],
                                          meta_config[c.session_key])
        self._all_conf_contents = {}
        self._get_division_settings = {}
        self._load_task_configs()

    def is_shc_member(self):
        return self._server_info.is_shc_member()

    def is_search_head(self):
        return self._server_info.is_search_head()

    def is_single_instance(self):
        return self._single_instance

    def get_meta_config(self):
        return self._meta_config

    def get_task_configs(self):
        return self._task_configs

    def get_all_conf_contents(self):
        return self._all_conf_contents

    def get_input_type(self):
        return self._input_type

    def _load_task_configs(self):
        inputs, configs, global_settings = th.get_all_conf_contents(
            self._meta_config["server_uri"],
            self._meta_config["session_key"],
            self._client_schema, self._input_type)
        if self._input_type:
            inputs = inputs.get(self._input_type)
        if not self._single_instance:
            inputs = [input for input in inputs if
                      input["name"] == self._stanza_name]
        all_task_configs = []
        for input in inputs:
            task_config = dict()
            task_config.update(input)
            task_config["__configs__"] = configs
            settings = dict()
            for setting in global_settings["settings"]:
                settings.update(setting)
            task_config["__settings__"] = settings
            if self.is_single_instance():
                collection_interval = "collection_interval"
                task_config[c.interval] = task_config.get(collection_interval)
            task_config[c.interval] = int(task_config[c.interval])
            if task_config[c.interval] <= 0:
                raise ValueError("The interval value {} is invalid. It "
                                    "should be a positive integer"
                                    .format(task_config[c.interval]))
            if self._server_info.is_search_head():
                task_config[c.use_kv_store] = True
            task_config[c.appname] = TaConfig._appname
            task_config[c.stanza_name] = task_config["name"]
            all_task_configs.append(task_config)
        self._task_configs = all_task_configs

    # Override this method if some transforms or validations needs to be done
    # before task_configs is exposed
    def process_task_configs(self, task_configs):
        pass


def create_ta_config(settings, config_cls=TaConfig, log_suffix=None,
                     single_instance=True):
    meta_config, configs = modinput.get_modinput_configs_from_stdin()
    stanza_name = None
    input_type = None
    if configs and "://" in configs[0].get("name", ""):
        input_type, stanza_name = configs[0].get("name").split("://",1)
    return config_cls(meta_config, settings, log_suffix, stanza_name,
                      input_type, single_instance=single_instance)
