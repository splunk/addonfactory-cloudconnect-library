import base64

from ..exception import ConfigException
from ..ext import lookup
from ..template import compile_template


class _Token(object):
    """Token class wraps a template expression"""

    def __init__(self, template_expr):
        self._render = compile_template(template_expr)

    def value(self, variables):
        return self._render(variables)


class Request(object):
    def __init__(self, options, pre_process, post_process,
                 checkpoint, repeat_mode):
        self._options = options
        self._pre_process = pre_process
        self._post_process = post_process
        self._checkpoint = checkpoint
        self._repeat_mode = repeat_mode

    @property
    def options(self):
        return self._options

    @property
    def pre_process(self):
        return self._pre_process

    @property
    def post_process(self):
        return self._post_process

    @property
    def repeat_mode(self):
        return self._repeat_mode

    @property
    def checkpoint(self):
        return self._checkpoint


class Authentication(object):
    def authenticate(self, headers, context):
        pass


class BasicAuthorization(Authentication):
    def __init__(self, options):
        if not options:
            raise ConfigException('options for basic auth unexpected to be empty')

        username = options.get('username')
        if not username:
            raise ConfigException('username is mandatory for basic auth')
        password = options.get('password')
        if not password:
            raise ConfigException('password is mandatory for basic auth')
        self._username = _Token(username)
        self._password = _Token(password)

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    def authenticate(self, headers, context):
        username = self._username.value(context)
        password = self._password.value(context)
        headers['Authorization'] = \
            'Basic %s' % base64.encodestring(username + ':' + password)


class Options(object):
    def __init__(self, url, method, header=None, auth=None, body=None):
        self._header = {k: _Token(v) for k, v in (header or {}).iteritems()}
        self._url = _Token(url)
        self._method = method.upper()
        self._auth = auth
        self._body = {k: _Token(v) for k, v in (body or {}).iteritems()}

    @property
    def header(self):
        return self._header

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method

    @property
    def auth(self):
        return self._auth

    @property
    def body(self):
        return self._body


class _Function(object):
    def __init__(self, inputs, function):
        self._inputs = [_Token(expr) for expr in (inputs or [])]
        self._function = function

    @property
    def inputs(self):
        return self._inputs

    def inputs_values(self, context):
        """
        Get rendered input values.
        """
        for it in self._inputs:
            yield it.value(context)

    @property
    def function(self):
        return self._function


class Task(_Function):
    def __init__(self, inputs, function, output=None):
        super(Task, self).__init__(inputs, function)
        self._output = output

    @property
    def output(self):
        return self._output

    def execute(self, context):
        args = [arg for arg in self.inputs_values(context)]
        caller = lookup(self.function)
        output = self._output

        if output is None:
            caller(*args)
            r = {}
        else:
            r = {output: caller(*args)}
        return r


class Condition(_Function):
    def calculate(self, context):
        args = [arg for arg in self.inputs_values(context)]
        caller = lookup(self.function)
        return caller(*args)


class _Conditional(object):
    def __init__(self, conditions):
        self._conditions = conditions or []

    @property
    def conditions(self):
        return self._conditions

    def passed(self, context):
        """
        Determine if current conditions are all passed.
        :param context: variables to render template
        :return: `True` if all passed else `False`
        """
        for condition in self._conditions:
            if not condition.calculate(context):
                return False
        return True


class Processor(_Conditional):
    def __init__(self, conditions, pipeline):
        super(Processor, self).__init__(conditions)
        self._pipeline = pipeline or []

    @property
    def pipeline(self):
        return self._pipeline


class RepeatMode(_Conditional):
    def __init__(self, loop_type, conditions):
        super(RepeatMode, self).__init__(conditions)
        self._type = loop_type

    @property
    def type(self):
        return self._type

    @property
    def conditions(self):
        return self._conditions

    def is_once(self):
        return self._type == 'once'


class Checkpoint(object):
    def __init__(self, namespace, contents):
        if not contents:
            raise ConfigException('checkpoint content unexpected to ne empty')
        self._namespace = [_Token(expr) for expr in (namespace or [])]
        self._content = {k: _Token(v) for k, v in contents.iteritems()}

    @property
    def namespace(self):
        return self._namespace

    @property
    def content(self):
        return self._content
