import logging

cc_logger = logging.getLogger("cloud_connect")
cc_logger_prefix = ''


def set_log(logger, logger_prefix=''):
    global cc_logger
    global cc_logger_prefix
    cc_logger = logger
    cc_logger_prefix = logger_prefix


def set_log_level(log_level):
    global cc_logger
    cc_logger.setLevel(log_level)


def critical(msg, *args, **kwargs):
    global cc_logger
    global cc_logger_prefix
    cc_logger.critical('{} {}'.format(cc_logger_prefix, msg), *args, **kwargs)


def error(msg, *args, **kwargs):
    global cc_logger
    global cc_logger_prefix
    cc_logger.error('{} {}'.format(cc_logger_prefix, msg), *args, **kwargs)


def exception(msg, *args, **kwargs):
    global cc_logger
    global cc_logger_prefix
    cc_logger.exception('{} {}'.format(cc_logger_prefix, msg), *args, **kwargs)


def warning(msg, *args, **kwargs):
    global cc_logger
    global cc_logger_prefix
    cc_logger.warning('{} {}'.format(cc_logger_prefix, msg), *args, **kwargs)

warn = warning

def info(msg, *args, **kwargs):
    global cc_logger
    global cc_logger_prefix
    cc_logger.info('{} {}'.format(cc_logger_prefix, msg), *args, **kwargs)


def debug(msg, *args, **kwargs):
    global cc_logger
    global cc_logger_prefix
    cc_logger.debug('{} {}'.format(cc_logger_prefix, msg), *args, **kwargs)
