import json
import os.path as op

from jsonschema import validate
from .models import Meta, GlobalSetting, Request

# JSON schema file path.
_SCHEMA_LOCATION = op.join(op.dirname(op.dirname(__file__)), 'configuration', 'hcm_schema.json')


class CloudConnectConfig(object):
    """
    A entity class to hold all configs loaded from JSON file.
    """

    def __init__(self, meta, global_settings, requests):
        self.meta = meta
        self.global_settings = global_settings
        self.requests = requests


def _load_schema_from_file(file_path):
    try:
        with open(file_path, 'r') as r:
            return json.loads(r.read())
    except:
        raise ValueError('Cannot load schema from {}'.format(file_path))


def load(file_path):
    if not op.isfile(file_path):
        raise ValueError('Invalid interface file {}'.format(file_path))
    try:
        with open(file_path, 'r') as r:
            return json.loads(r.read())
    except:
        raise ValueError('Cannot load JSON interface from file {}'.format(file_path))


def load_cloud_connect_config(json_file_path):
    """
    Load JSON based interface from a file path and validate it with schema.
    :param json_file_path: file path of json based interface.
    :return: A `CloudConnectConfig` object.
    """
    definition = load(json_file_path)
    validate(definition, _load_schema_from_file(_SCHEMA_LOCATION))

    meta = Meta(definition['meta'])
    gs = GlobalSetting(definition['global_settings'])
    requests = [Request(r) for r in definition['requests']]
    conf = CloudConnectConfig(meta=meta, global_settings=gs, requests=requests)
    return conf


if __name__ == '__main__':
    config = load_cloud_connect_config('../../../example/json_interface/okta_after_hcm.json')
    print config.meta.version
