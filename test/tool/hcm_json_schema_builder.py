import jsl

_HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

_DATA_FORMAT = ['splunk_xml', 'raw']

_STOP_CONDITIONS = ['empty', 'once']
_DEFAULT_STOP_CONDITION = 'empty'

_AUTH_TYPES = ['digest', 'basic64']


class _Output(jsl.Document):
    """
    Represents the common schema definition for outputting configuration.
    """

    class Options(object):
        additional_properties = True

    data = jsl.DictField(required=True,
                         properties={
                             'format': jsl.StringField(enum=_DATA_FORMAT,
                                                       required=True),
                             'source_key': jsl.StringField(required=True),
                         },
                         additional_properties=True)


class _FileOutput(_Output):
    """
    Represents scheme for file outputting configuration which type must
     be `file` and user can specify file destination, etc in options.
    """
    type = jsl.StringField(enum=['file'])
    options = jsl.DictField(required=True)


class _StdoutOutput(_Output):
    """
    Represents scheme for stdout outputting configuration.
    """
    type = jsl.StringField(enum=['stdout'], required=True)
    options = jsl.DictField(required=True,
                            properties={
                                'host': jsl.StringField(required=True),
                                'index': jsl.StringField(required=True),
                                'source': jsl.StringField(required=True),
                                'sourcetype': jsl.StringField(required=True),
                            },
                            additionalProperties=True)


class _Checkpoint(jsl.Document):
    """
    Represents configuration scheme for saving checkpoint.
    """

    class Options(object):
        additional_properties = True

    save = jsl.BooleanField(required=False, default=True)

    namespace = jsl.ArrayField(items=[jsl.StringField()],
                               required=False)
    content = jsl.DictField(required=True)


class _Request(jsl.Document):
    """
    Represents config scheme for single request.
    """

    class Options(object):
        additional_properties = True

    context = jsl.DictField(required=True)

    auth = jsl.DictField(required=False,
                         properties={
                             'type': jsl.StringField(enum=_AUTH_TYPES,
                                                     required=True),
                             'options': jsl.DictField(),
                         },
                         additional_properties=True)

    headers = jsl.DictField(required=True)
    url = jsl.UriField(required=True)
    method = jsl.StringField(enum=_HTTP_METHODS, required=True)

    stop_condition = jsl.StringField(enum=_STOP_CONDITIONS,
                                     required=True,
                                     default=_DEFAULT_STOP_CONDITION)
    output = jsl.ArrayField(
        items=jsl.OneOfField([jsl.DocumentField(_StdoutOutput, as_ref=True),
                              jsl.DocumentField(_FileOutput, as_ref=True)]),
        min_items=1
    )
    params = jsl.DictField(required=True)
    checkpoint = jsl.DocumentField(_Checkpoint, as_ref=True)


class _Proxy(jsl.Document):
    """
    Represents proxy configuration scheme. enabled, host and port are required.
    """

    class Options(object):
        additional_properties = True

    enabled = jsl.OneOfField([jsl.BooleanField(), jsl.StringField()],
                             required=True)

    host = jsl.StringField(required=True)
    port = jsl.OneOfField([jsl.IntField(), jsl.StringField()],
                          required=True)
    username = jsl.StringField(required=False)
    password = jsl.StringField(required=False)
    rdns = jsl.StringField(required=False)
    type = jsl.StringField(required=False)


class Schema(jsl.Document):
    """
    Represents scheme for validating user configuration as JSON format.
    """
    __version__ = jsl.StringField(required=True, pattern='[\d\.]+')
    parameters = jsl.ArrayField(required=True, items=[jsl.StringField()])

    proxy = jsl.DocumentField(_Proxy, required=False, as_ref=True)

    hec = jsl.DictField(required=True)
    logging = jsl.DictField(required=True)
    requests = jsl.ArrayField(items=[jsl.DocumentField(_Request, as_ref=True)],
                              min_items=1,
                              required=True)
