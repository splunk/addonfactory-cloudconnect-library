from .data_collection.ta_data_client import TaDataClient
from ..common import splunk_util
from ..splunktacollectorlib.common import log as stulog
from ..splunktacollectorlib.data_collection import ta_consts as c
from ..common.log import set_cc_logger


class TACloudConnectClient(TaDataClient):
    def __init__(self,
                 meta_config,
                 task_config,
                 ckpt=None,
                 checkpoint_mgr=None,
                 event_write_fn=None
                 ):
        super(TACloudConnectClient, self).__init__(meta_config,
                                                   task_config,
                                                   ckpt,
                                                   checkpoint_mgr,
                                                   event_write_fn)
        self._set_log()
        self._cc_config_file = self._meta_config["cc_json_file"]
        from ..client import CloudConnectClient as Client
        self._client = Client(self._task_config, self._cc_config_file)
        splunk_util.set_std_out(event_write_fn)
        splunk_util.set_check_pointer(checkpoint_mgr)

    def _set_log(self):
        pairs = ['{}="{}"'.format(c.stanza_name, self._task_config[
            c.stanza_name])]
        set_cc_logger(stulog.logger,
                          logger_prefix="[{}]".format(" ".join(pairs)))

    def is_stopped(self):
        return self._stop

    def stop(self):
        self._stop = True
        self._client.stop()

    def get(self):
        self._client.start()
        raise StopIteration