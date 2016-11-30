import json
import os.path as op

import pytest

from jsonschema import ValidationError
from jsonschema import validate


def _load_json(json_file):
    current_dir = op.dirname(op.abspath(__file__))
    with open(op.join(current_dir, 'data', json_file), 'r') as f:
        return json.loads(f.read())


def _load_schema_from_file():
    schema_file = op.join(op.dirname(op.dirname(op.dirname(op.abspath(__file__)))),
                          'package', 'lib-cloud-connect', 'configuration', 'schema.json')
    with open(schema_file, 'r') as f:
        return json.loads(f.read())


def test_validate_generated_schema():
    conf = _load_json('test_1.json')
    assert conf['meta']['version'] == '1.0.0'
    validate(conf, _load_schema_from_file())


def test_validate_schema_expect_raise():
    conf = {}
    schema = _load_schema_from_file()

    with pytest.raises(ValidationError):
        validate(conf, schema)

    # validate all required elements in top level
    required = ['meta', 'parameters', 'requests']
    validated = _load_json('test_1.json')

    for r in required:
        backup = validated[r]
        del validated[r]
        with pytest.raises(ValidationError):
            validate(validated, schema)
        validated[r] = backup
