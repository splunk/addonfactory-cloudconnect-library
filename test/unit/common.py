import os.path as op

EXAMPLE_DIR = op.join(op.dirname(op.dirname(op.dirname(__file__))), 'examples', '1.0')
DATA_DIR = op.join(op.dirname(op.dirname(__file__)), 'data')
SCHEMA_FILE = op.join(op.dirname(op.dirname(op.dirname(op.abspath(__file__)))),
                      'package', 'cloudconnectlib', 'configuration', 'schema_1_0_0.json')
