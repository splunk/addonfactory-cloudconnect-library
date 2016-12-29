import os.path as op

PROJECT_ROOT = op.dirname(op.dirname(op.dirname(op.abspath(__file__))))

EXAMPLE_DIR = op.join(PROJECT_ROOT, 'examples', '1.0')
TEST_DATA_DIR = op.join(PROJECT_ROOT, 'test', 'data')
CONFIGURATION_DIR = op.join(PROJECT_ROOT, 'package', 'cloudconnectlib', 'configuration')
SCHEMA_FILE = op.join(CONFIGURATION_DIR, 'schema_1_0_0.json')
