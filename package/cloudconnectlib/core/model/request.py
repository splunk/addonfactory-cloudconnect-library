from ..exception import ConfigException
from ..template import compile_template


class _Token(object):
    """Token class wraps a template expression"""

    def __init__(self, template_expr):
        self._render = compile_template(template_expr)

    def value(self, variables):
        return self._render(variables)


class Request(object):
    def __init__(self, options, before_request, skip_after_request,
                 after_request, checkpoint, loop_mode):
        self._options = options
        self._before_request = before_request
        self._skip_after_request = skip_after_request
        self._after_request = after_request
        self._checkpoint = checkpoint
        self._loop_mode = loop_mode

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

    @property
    def loop_mode(self):
        return self._loop_mode


class BasicAuthorization(object):
    def __init__(self, options):
        if not options:
            raise ConfigException('options for basic auth expect to be not none')

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
        return self.password


class Options(object):
    def __init__(self, url, method, header=None, auth=None):
        self._header = header
        self._url = _Token(url)
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


class _Function(object):
    def __init__(self, inputs, function):
        self._inputs = [_Token(expr) for expr in (inputs or [])]
        self._function = function

    @property
    def inputs(self):
        return self._inputs

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


class Processor(object):
    def __init__(self, tasks):
        self._tasks = tasks

    @property
    def tasks(self):
        return self._tasks


class BeforeRequest(Processor):
    pass


class AfterRequest(Processor):
    pass


class Condition(_Function):
    pass


class SkipAfterRequest(object):
    def __init__(self, conditions):
        self._conditions = conditions or []

    @property
    def conditions(self):
        return self._conditions


class LoopMode(object):
    def __init__(self, loop_type, conditions=None):
        self._type = loop_type
        self._conditions = conditions or []

    @property
    def type(self):
        return self._type

    @property
    def conditions(self):
        return self._conditions


class Checkpoint(object):
    def __init__(self, namespace, contents):
        if not contents:
            raise ConfigException('checkpoint content expect to not empty')
        self._namespace = [_Token(expr) for expr in (namespace or [])]
        self._content = {k: _Token(v) for k, v in contents.iteritems()}

    @property
    def namespace(self):
        return self._namespace

    @property
    def content(self):
        return self._content
