import base64

from .ext import lookup_method
from .template import compile_template
from ..common.log import get_cc_logger

_logger = get_cc_logger()


class _Token(object):
    """Token class wraps a template expression"""

    def __init__(self, template_expr):
        self._render = compile_template(template_expr)

    def value(self, variables):
        return self._render(variables)


class _DictToken(object):
    """DictToken wraps a dict which value is template expression"""

    def __init__(self, template_expr):
        self._tokens = {k: _Token(v)
                        for k, v in (template_expr or {}).iteritems()}

    def value(self, variables):
        return {k: v.value(variables) for k, v in self._tokens.iteritems()}


class BaseAuth(object):
    """A base class for all authorization classes"""

    def __call__(self, headers, context):
        raise NotImplementedError('Auth must be callable.')


class BasicAuthorization(BaseAuth):
    """BasicAuthorization class implements basic auth"""

    def __init__(self, options):
        if not options:
            raise ValueError('Options for basic auth unexpected to be empty')

        username = options.get('username')
        if not username:
            raise ValueError('Username is mandatory for basic auth')
        password = options.get('password')
        if not password:
            raise ValueError('Password is mandatory for basic auth')

        self._username = _Token(username)
        self._password = _Token(password)

    def __call__(self, headers, context):
        username = self._username.value(context)
        password = self._password.value(context)
        headers['Authorization'] = 'Basic %s' % base64.encodestring(
            username + ':' + password
        ).strip()


class Options(object):
    def __init__(self, url, method, header=None, auth=None, body=None):
        self._header = _DictToken(header)
        self._url = _Token(url)
        self._method = method.upper()
        self._auth = auth
        self._body = _DictToken(body)

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

    def normalize_url(self, context):
        return self._url.value(context)

    def normalize_header(self, context):
        return self.header.value(context)

    def normalize_body(self, context):
        return self.body.value(context)


class _Function(object):
    def __init__(self, inputs, function):
        self._inputs = tuple(_Token(expr) for expr in inputs or [])
        self._function = function

    @property
    def inputs(self):
        return self._inputs

    def inputs_values(self, context):
        """
        Get rendered input values.
        """
        for arg in self._inputs:
            yield arg.value(context)

    @property
    def function(self):
        return self._function


class Task(_Function):
    """Task class wraps a task in processor pipeline"""

    def __init__(self, inputs, function, output=None):
        super(Task, self).__init__(inputs, function)
        self._output = output

    @property
    def output(self):
        return self._output

    def execute(self, context):
        """Execute task with arguments which rendered from context """
        args = [arg for arg in self.inputs_values(context)]
        caller = lookup_method(self.function)
        output = self._output

        _logger.info(
            'Executing task method: [%s], input size: [%s], output: [%s]',
            self.function, len(args), output
        )

        if output is None:
            caller(*args)
            return {}

        return {output: caller(*args)}


class Condition(_Function):
    """A condition return the value calculated from input and function"""

    def calculate(self, context):
        args = [arg for arg in self.inputs_values(context)]
        caller = lookup_method(self.function)
        return caller(*args)


class _Conditional(object):
    """A base class for all conditional action"""

    def __init__(self, conditions):
        self._conditions = conditions or []

    @property
    def conditions(self):
        return self._conditions

    def passed(self, context):
        """Determine if any condition is satisfied.
        :param context: variables to render template
        :return: `True` if all passed else `False`
        """
        return any(
            condition.calculate(context) for condition in self._conditions)


class Processor(_Conditional):
    """Processor class contains a conditional data process pipeline"""

    def __init__(self, skip_conditions, pipeline):
        super(Processor, self).__init__(skip_conditions)
        self._pipeline = pipeline or []

    @property
    def pipeline(self):
        return self._pipeline

    def should_skipped(self, context):
        """Determine processor if should skip process"""
        return self.passed(context)


class IterationMode(_Conditional):
    def __init__(self, iteration_count, conditions):
        super(IterationMode, self).__init__(conditions)
        self._iteration_count = iteration_count

    @property
    def iteration_count(self):
        return self._iteration_count

    @property
    def conditions(self):
        return self._conditions


class Checkpoint(object):
    """A checkpoint includes a namespace to determine the checkpoint location
    and a content defined the format of content stored in checkpoint."""

    def __init__(self, namespace, content):
        """Constructs checkpoint with given namespace and content template. """
        if not content:
            raise ValueError('Checkpoint content must not be empty')

        self._namespace = tuple(_Token(expr) for expr in namespace or ())
        self._content = _DictToken(content)

    @property
    def namespace(self):
        return self._namespace

    def normalize_namespace(self, ctx):
        """Normalize namespace with context used to render template."""
        return [token.value(ctx) for token in self._namespace]

    @property
    def content(self):
        return self._content

    def normalize_content(self, ctx):
        """Normalize checkpoint with context used to render template."""
        return self._content.value(ctx)
