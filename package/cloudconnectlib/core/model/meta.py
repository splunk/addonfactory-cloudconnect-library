class Meta(object):
    def __init__(self, meta_config):
        self._version = meta_config.get("version")

    @property
    def version(self):
        return self._version

