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
    method = StringField(enum=_HTTP_METHODS, default='GET')
    headers = DictField()

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


class IterationMode(Document):
    iteration_count = OneOfField(
        fields=[StringField(pattern='^[+-]?[1-9]\d*|0$'), IntField()])
    stop_conditions = ArrayField(DocumentField(Condition))


class Processor(Document):
    skip_conditions = ArrayField(DocumentField(Condition))
    pipeline = ArrayField(DocumentField(Task))


class Request(Document):
    """
    Represents config scheme for single request.
    """
    request = DocumentField(Options, required=True)
    pre_process = DocumentField(Processor)
    post_process = DocumentField(Processor, required=True)
    iteration_mode = DocumentField(IterationMode, as_ref=True, required=True)
    checkpoint = DocumentField(Checkpoint, as_ref=True)


class Proxy(Document):
    """
    Represents proxy configuration scheme. enabled, host and port are required.
    """
    # 'enabled' can be string or int or boolean
    enabled = OneOfField(fields=[StringField(), BooleanField(), IntField()],
                         default=False)

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
    apiVersion = StringField(required=True, pattern='(?:\d{1,3}\.){2}[\w\-]{1,15}')


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
    tokens = ArrayField(StringField(), required=True)

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
                           'cloudconnectlib', 'configuration', 'schema_1_0_0.json')
    schema_as_json = build_schema(True)
    with open(schema_file, 'w+') as f:
        f.write(json.dumps(schema_as_json, indent=4))
