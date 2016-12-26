"""
APP Cloud Connect
"""
import os
import os.path as op

from .common.lib_util import register_cacert_locater
from .splunktacollectorlib.mod_helper import get_main_file

register_cacert_locater(os.path.join(os.path.dirname(__file__), 'core', 'cacerts'))
import ca_certs_locater


def _set_cert_file_dir():
    # Set temp cert file location to local
    ca_certs_locater.TEMP_CERT_FILE_DIR = op.join(
        op.dirname(op.dirname(get_main_file())), 'local'
    )


_set_cert_file_dir()

__version__ = '1.0.0'
