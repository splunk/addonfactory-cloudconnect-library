import os.path as op

from cloudconnectlib.common.log import set_cc_logger
from cloudconnectlib.splunktacollectorlib.common import log as stulog

# FIXME
set_cc_logger(stulog.logger, '')

PROJECT_ROOT = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))

EXAMPLE_DIR = op.join(PROJECT_ROOT, 'examples', '1.0')
TEST_DATA_DIR = op.join(PROJECT_ROOT, 'test', 'data')
CONFIGURATION_DIR = op.join(PROJECT_ROOT, 'package', 'cloudconnectlib', 'configuration')
SCHEMA_FILE = op.join(CONFIGURATION_DIR, 'schema_1_0_0.json')
