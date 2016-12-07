import json
import os.path as op
from collections import OrderedDict

from jsl import (
    ArrayField,
    BooleanField,
    DictField,
    Document,
    DocumentField,
    IntField,
    OneOfField,
    StringField,
)

_HTTP_METHODS = ['GET', 'POST']
_AUTH_TYPES = ['digest', 'basic_auth']


class Checkpoint(Document):
    """
    Represents configuration scheme for saving checkpoint.
    """
    namespace = ArrayField(items=StringField())
    content = DictField(required=True)


class Authentication(Document):
    type = StringField(enum=_AUTH_TYPES, required=True)
    options = DictField()


class Options(Document):
    # required
    url = StringField(required=True)
    method = StringField(enum=_HTTP_METHODS, required=True)
    headers = DictField(required=True)

    # optional
    auth = DocumentField(Authentication, as_ref=True)
    body = DictField()


class Function(Document):
    input = ArrayField(items=StringField(), required=True)
    method = StringField(required=True)


class Task(Function):
    output = StringField()


class Condition(Function):
    pass


class RepeatMode(Document):
    type = StringField(enum=['loop', 'once'], required=True)
    stop_conditions = ArrayField(DocumentField(Condition, as_ref=True),
                                 min_items=1)


class Processor(Document):
    conditions = ArrayField(DocumentField(Condition, as_ref=True))
    pipeline = ArrayField(DocumentField(Task), as_ref=True)


class Request(Document):
    """
    Represents config scheme for single request.
    """
    options = DocumentField(Options, as_ref=True, required=True)
    pre_process = DocumentField(Processor, as_ref=True, required=True)
    post_process = DocumentField(Processor, as_ref=True, required=True)
    repeat_mode = DocumentField(RepeatMode, as_ref=True, required=True)
    checkpoint = DocumentField(Checkpoint, as_ref=True, required=True)


class Proxy(Document):
    """
    Represents proxy configuration scheme. enabled, host and port are required.
    """
    # 'enabled' can be string or int or boolean
    enabled = OneOfField(fields=[StringField(), BooleanField(), IntField()],
                         required=True)

    host = StringField(required=True)
    port = OneOfField(fields=[StringField(), IntField(minimum=1,
                                                      maximum=65535,
                                                      exclusive_minimum=True,
                                                      exclusive_maximum=True)],
                      required=True)

    username = StringField()
    password = StringField()
    rdns = StringField()
    type = StringField()


class Meta(Document):
    """
    Represents scheme of metadata which contains version, etc.
    """
    version = StringField(required=True, pattern='(?:\d{1,3}\.){2}[\w\-]{1,15}')


class GlobalSettings(Document):
    """
    Represents scheme of global settings which contains logging, proxy etc.
    """

    proxy = DocumentField(Proxy, as_ref=True)
    logging = DictField(properties={
        'level': StringField(),
    })


class Schema(Document):
    """
    Represents scheme for validating user configuration as JSON format.
    """

    meta = DocumentField(Meta, as_ref=True, required=True)
    parameters = ArrayField(StringField(), required=True)

    global_settings = DocumentField(GlobalSettings, as_ref=True)
    requests = ArrayField(DocumentField(Request, as_ref=True),
                          min_items=1,
                          required=True)


def build_schema(ordered=True):
    """
    Builds a schema object for validating JSON based interface.

    :param ordered:
        Whether order the elements in schema.
    :type ordered: `bool`
    :return:
        A schema object as dict.
    :rtype: `OrderedDict`
    """
    schema = json.dumps(Schema.get_schema(ordered=ordered))
    prefix_erased = schema.replace(__name__ + '.', '')
    return json.loads(prefix_erased, object_pairs_hook=OrderedDict)


if __name__ == '__main__':
    schema_file = op.join(op.dirname(op.dirname(op.dirname(op.abspath(__file__)))),
                          'package', 'cloudconnectlib', 'configuration', 'schema.json')
    schema_as_json = build_schema(True)
    with open(schema_file, 'w') as f:
        f.write(json.dumps(schema_as_json, indent=2))
