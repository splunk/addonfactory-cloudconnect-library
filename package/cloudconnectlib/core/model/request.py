from ..exception import InvalidConfigException
from ..ext import lookup
from ..template import CloudConnectTemplate as Template


class TokenizedObject(object):
    def __init__(self, template):
        self._template = template
        self._jtemplate = Template(template)

    def value(self, context):
        return self._value

    def render_value(self, context):
        return self.set_value(self._jtemplate.render(context))

    def set_value(self, current_value):
        self._value = current_value
        return self._value


class Request(object):
    def __init__(self, options, before_request, skip_after_request,
                 after_request, checkpoint):
        self._options = options
        self._before_request = before_request
        self._skip_after_request = skip_after_request
        self._after_request = after_request
        self._checkpoint = checkpoint

    @property
    def options(self):
        return self._options

    @property
    def before_request(self):
        return self._before_request

    @property
    def skip_after_request(self):
        return self._skip_after_request

    @property
    def after_request(self):
        return self._after_request

    @property
    def checkpoint(self):
        return self._checkpoint


class Header(object):
    def __init__(self):
        self._items = dict()

    def add(self, key, value):
        self._items[key] = TokenizedObject(value)

    def get(self, key):
        return self._items.get(key)

    @property
    def items(self):
        return self._items

    def build(self, context):
        header = {}
        for k in self._items:
            header[k] = self.get(k).render_value(context)
        return header


class BasicAuthorization(object):
    def __init__(self, options):
        if not options:
            raise InvalidConfigException("the options field of auth is empty")
        self._username = options.get("username")
        self._password = options.get("password")
        if not self._username:
            raise InvalidConfigException("username of auth is empty")
        if not self._password:
            raise InvalidConfigException("password of auth is empty")
        self._username = TokenizedObject(self._username)
        self._password = TokenizedObject(self._password)

    @property
    def username(self):
        return self._username

    def get_username(self, ctx):
        return self._username.render_value(ctx)

    def get_password(self, ctx):
        return self._password.render_value(ctx)

    @property
    def password(self):
        return self.password


class Options(object):
    def __init__(self, url, header=None, method="GET", auth=None):
        self._header = header
        self._url = TokenizedObject(url)
        self._method = method.upper()
        self._auth = auth

    @property
    def header(self):
        return self._header

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method


class ProcessHandler(object):
    def __init__(self, inputs, method):
        self._inputs = []
        for item in inputs:
            self._inputs.append(TokenizedObject(item))
        self._method = method

    @property
    def inputs(self):
        return self._inputs

    def inputs_values(self, context):
        """
        Get rendered input values.
        """
        for it in self._inputs:
            yield it.render_value(context)

    @property
    def method(self):
        return self._method


class BeforeRequest(ProcessHandler):
    def __init__(self, inputs, method, output=None):
        super(BeforeRequest, self).__init__(inputs, method)
        self._output = output

    @property
    def output(self):
        return self._output


class AfterRequest(BeforeRequest):
    pass


class Condition(ProcessHandler):
    def calculate(self, context):
        """
        Calculates condition result with input and method.
        :return: `True` if condition meets.
        """
        method = lookup(self.method)
        if method is None:
            raise ValueError('method {} is not exist'.format(self.method))
        args = [it for it in self.inputs_values(context)]
        return method(*args)


class SkipAfterRequest(object):
    def __init__(self):
        self._conditions = []

    def add_condition(self, condition):
        self._conditions.append(condition)

    @property
    def conditions(self):
        return self._conditions


class LoopMode(object):
    loop_types = ["loop", "once"]

    def __init__(self, type="once", conditions=None):
        if type.lower() in LoopMode.loop_types:
            self._type = type
        else:
            self._type = "once"
        self._conditions = conditions

    @property
    def type(self):
        return self._type

    @property
    def conditions(self):
        return self._conditions


class Checkpoint(object):
    def __init__(self, contents, keys=None):
        self._namespace = []
        if keys:
            for key in keys:
                self._namespace.append(TokenizedObject(key))
        if not contents:
            raise InvalidConfigException("the content field of checkpoint is empty")
        self._content = dict()
        for key, value in contents.iteritems():
            self._content[key] = TokenizedObject(value)

    @property
    def namespace(self):
        return self._namespace

    @property
    def content(self):
        return self._content
