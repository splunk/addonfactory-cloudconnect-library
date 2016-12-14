import os
import sys
import platform
from ..splunktacollectorlib.common import log as stulog
import re


def register_module(new_path):
    """ register_module(new_path): adds a directory to sys.path.
    Do nothing if it does not exist or if it's already in sys.path.
    """
    if not os.path.exists(new_path):
        return

    new_path = os.path.abspath(new_path)
    if platform.system() == 'Windows':
        new_path = new_path.lower()
    for x in sys.path:
        x = os.path.abspath(x)
        if platform.system() == 'Windows':
            x = x.lower()
        if new_path in (x, x + os.sep):
            return
    sys.path.insert(0, new_path)


def register_cacert_locater(cacerts_locater_path):
    _HTTPLIB_PATTERN = re.compile(r'(?:\w+.)*httplib$')
    for x in sys.modules:
        if re.match(_HTTPLIB_PATTERN, x):
            stulog.logger.warning("Httplib module '{}' is already installed. "
                         "The ca_certs_locater may not work".format(x))
    register_module(cacerts_locater_path)
