import logging
from solnlib.pattern import Singleton


def set_cc_logger(logger, logger_prefix=""):
    CloudClientLogAdapter(logger, prefix=logger_prefix)


def get_cc_logger():
    return CloudClientLogAdapter()


class CloudClientLogAdapter(logging.LoggerAdapter):

    __metaclass__ = Singleton

    def __init__(self, logger=None, extra=None, prefix=""):
        super(CloudClientLogAdapter, self).__init__(logger, extra)
        self.cc_prefix = prefix if prefix else ""

    def process(self, msg, kwargs):
        msg = "{} {}".format(self.cc_prefix, msg)
        return super(CloudClientLogAdapter, self).process(msg, kwargs)

    def set_level(self, val):
        self.logger.setLevel(val)
