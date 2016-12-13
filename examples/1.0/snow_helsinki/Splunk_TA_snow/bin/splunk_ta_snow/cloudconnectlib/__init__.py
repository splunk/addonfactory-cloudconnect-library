"""
APP Cloud Connect
"""
import os
import sys

def register_module(new_path):
    """ register_module(new_path): adds a directory to sys.path.
    Do nothing if it does not exist or if it's already in sys.path.
    """
    if not os.path.exists(new_path):
        return

    new_path = os.path.abspath(new_path)
    if sys.platform == 'win32':
        new_path = new_path.lower()

    for x in sys.path:
        x = os.path.abspath(x)
        if sys.platform == 'win32':
            x = x.lower()
        if new_path in (x, x + os.sep):
            return
    sys.path.insert(0, new_path)

#import httplib2 cert loader
register_module(os.path.join(os.path.dirname(__file__), 'core', 'cacerts'))

from .client import CloudConnectClient
__version__ = '1.0'
