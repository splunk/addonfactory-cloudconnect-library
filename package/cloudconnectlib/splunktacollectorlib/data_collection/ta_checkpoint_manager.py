from . import ta_consts as c
from ...splunktalib import state_store as ss
from ..common import log as stulog
from . import ta_helper as th


class TACheckPointMgr(object):
    SEPARATOR = "_" * 3

    def __init__(self, meta_config, task_config):
        self._task_config = task_config
        self._store = ss.get_state_store(
            meta_config,
            task_config[c.appname],
            use_kv_store=self._use_kv_store())

    def _use_kv_store(self):
        use_kv_store = self._task_config.get(
            c.use_kv_store, False)
        if use_kv_store:
            stulog.logger.info("Stanza={} Using KV store for checkpoint"
                               .format(self._task_config[c.stanza_name]))
        return use_kv_store

    def get_ckpt_key(self, namespaces=None):
        return self._key_formatter(namespaces)

    def get_ckpt(self, namespaces=None, show_namespaces=False):
        key, namespaces = self.get_ckpt_key(namespaces)
        raw_checkpoint = self._store.get_state(key)
        if not show_namespaces and raw_checkpoint:
            return raw_checkpoint.get("data")
        return raw_checkpoint

    def update_ckpt(self, ckpt, namespaces=None):
        if not ckpt:
            stulog.logger.warning("Checkpoint expect to be not empty.")
            return
        key, namespaces = self.get_ckpt_key(namespaces)
        self._store.update_state(key, {"namespaces": namespaces, "data": ckpt})

    def remove_ckpt(self, namespaces=None):
        key, namespaces = self.get_ckpt_key(namespaces)
        self._store.delete_state(key)

    def _key_formatter(self, namespaces=None):
        if not namespaces:
            stulog.logger.info('Namespaces is empty, using stanza name instead.')
            namespaces = [self._task_config[c.stanza_name]]
        key_str = TACheckPointMgr.SEPARATOR.join(namespaces)
        hashed_file = th.format_name_for_file(key_str)
        stulog.logger.info('raw file=%s hashed file=%s', key_str, hashed_file)
        return hashed_file, namespaces
