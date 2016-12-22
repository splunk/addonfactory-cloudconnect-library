import os.path as op

from package.cloudconnectlib.common.log import set_cc_logger
from package.cloudconnectlib.splunktacollectorlib.common import log as stulog

# FIXME
set_cc_logger(stulog.logger, '')

EXAMPLE_DIR = op.join(op.dirname(op.dirname(op.dirname(__file__))), 'examples', '1.0')
DATA_DIR = op.join(op.dirname(op.dirname(__file__)), 'data')

CONFIGURATION_DIR = op.join(op.dirname(op.dirname(op.dirname(op.abspath(__file__)))),
                            'package', 'cloudconnectlib', 'configuration')
SCHEMA_FILE = op.join(CONFIGURATION_DIR, 'schema_1_0_0.json')
