import json

from . import ta_consts as c
from . import ta_helper as th
from ..common import log as stulog
from ...splunktalib import state_store as ss
from ...splunktalib.common.util import is_true


class TACheckPointMgr(object):
    SEPARATOR = "_" * 3

    def __init__(self, meta_config, task_config):
        self._task_config = task_config
        use_kv_store = self._use_kv_store()
        use_cache_file = self._use_cache_file() if not use_kv_store else False

        self._store = ss.get_state_store(
            meta_config,
            task_config[c.appname],
            use_kv_store=use_kv_store,
            use_cache_file=use_cache_file
        )

    def _use_kv_store(self):
        use_kv_store = is_true(self._task_config.get(c.use_kv_store, False))
        if use_kv_store:
            stulog.logger.info(
                "Stanza=%s Using KV store for checkpoint",
                self._task_config[c.stanza_name]
            )
        return use_kv_store

    def _use_cache_file(self):
        use_cache_file = is_true(self._task_config.get(c.use_cache_file, True))
        if use_cache_file:
            stulog.logger.info(
                "Stanza=%s using cached file store to create checkpoint",
                self._task_config[c.stanza_name]
            )
        return use_cache_file

    def get_ckpt_key(self, namespaces=None):
        return self._key_formatter(namespaces)

    def get_ckpt(self, namespaces=None, show_namespaces=False):
        key, namespaces = self.get_ckpt_key(namespaces)
        raw_checkpoint = self._store.get_state(key)
        stulog.logger.info("Get checkpoint key='{}' value='{}'"
                           .format(key, json.dumps(raw_checkpoint)))
        if not show_namespaces and raw_checkpoint:
            return raw_checkpoint.get("data")
        return raw_checkpoint

    def update_ckpt(self, ckpt, namespaces=None):
        if not ckpt:
            stulog.logger.warning("Checkpoint expect to be not empty.")
            return
        key, namespaces = self.get_ckpt_key(namespaces)
        value = {"namespaces": namespaces, "data": ckpt}
        stulog.logger.info("Update checkpoint key='{}' value='{}'"
                           .format(key, json.dumps(value)))
        self._store.update_state(key, value)

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

    def close(self, key=None):
        try:
            self._store.close(key)
            stulog.logger.info('Closed state store successfully. key=%s', key)
        except Exception:
            stulog.logger.exception('Error closing state store. key=%s', key)
