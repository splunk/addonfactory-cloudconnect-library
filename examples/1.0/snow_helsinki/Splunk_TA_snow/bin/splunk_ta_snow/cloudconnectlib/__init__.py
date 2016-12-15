"""
APP Cloud Connect
"""
from .common.lib_util import register_cacert_locater
import os

register_cacert_locater(os.path.join(os.path.dirname(__file__), 'core', 'cacerts'))

__version__ = '1.0.0'

