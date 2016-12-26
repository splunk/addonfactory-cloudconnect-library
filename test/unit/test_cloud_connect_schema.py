import json
import os.path as op
from os import listdir

import common
import pytest
from jsonschema import ValidationError
from jsonschema import validate


def _json_file(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)


def _load_json_under_data(json_file):
    return _json_file(op.join(common.TEST_DATA_DIR, json_file))


def _load_schema_from_file():
    with open(common.SCHEMA_FILE, 'r') as f:
        return json.loads(f.read())


def test_validate_generated_schema():
    conf = _load_json_under_data('test_1.json')
    assert conf['meta']['apiVersion'] == '1.0.0'
    validate(conf, _load_schema_from_file())


def test_validate_schema_expect_raise():
    conf = {}
    schema = _load_schema_from_file()

    with pytest.raises(ValidationError):
        validate(conf, schema)

    # validate all required elements in top level
    required = ['meta', 'tokens', 'requests']
    validated = _load_json_under_data('test_1.json')

    for r in required:
        backup = validated[r]
        del validated[r]
        with pytest.raises(ValidationError):
            validate(validated, schema)
        validated[r] = backup


def test_validate_examples():
    files = [f for f in listdir(common.EXAMPLE_DIR) if
             op.isfile(op.join(common.EXAMPLE_DIR, f)) and f.endswith('.json')]
    schema = _load_schema_from_file()

    for f in files:
        validate(schema, _json_file(op.join(common.EXAMPLE_DIR, f)))
