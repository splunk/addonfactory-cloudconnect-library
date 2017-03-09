import json
from abc import abstractmethod

from cloudconnectlib.common.log import get_cc_logger
from cloudconnectlib.core import defaults
from cloudconnectlib.core.exceptions import HTTPError
from cloudconnectlib.core.exceptions import StopCCEIteration
from cloudconnectlib.core.ext import lookup_method
from cloudconnectlib.core.http import get_proxy_info, HttpClient
from cloudconnectlib.core.models import DictToken, _Token

logger = get_cc_logger()

_RESPONSE_KEY = '__response__'


class ProcessHandler(object):
    def __init__(self, method, arguments, output):
        self.method = method
        self.callable_method = lookup_method(method)
        self.arguments = [_Token(arg) for arg in arguments or ()]
        self.output = output

    def execute(self, context):
        args = [arg.render(context) for arg in self.arguments]
        logger.debug('% arguments found for method %s', len(args), self.method)
        self.callable_method(*args)


class Condition(object):
    def __init__(self, method, arguments):
        self.method = method
        self.callable_method = lookup_method(method)
        self.arguments = [_Token(arg) for arg in arguments or ()]

    def passed(self, context):
        args = [arg.render(context) for arg in self.arguments]
        logger.debug('% arguments found for method %s', len(args), self.method)
        return self.callable_method(args)


class ConditionGroup(object):
    def __init__(self):
        self._conditions = []

    def add(self, condition):
        self._conditions.append(condition)

    def passed(self, context):
        return any(
            cdn.passed(context) for cdn in self._conditions
        )


class Request(object):
    def __init__(self, method, url, headers, body):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = json.dumps(body) if body else None


class RequestWithToken(object):
    def __init__(self, request):
        if not request:
            raise ValueError('The request is none')
        url = request.get('url')
        if not url:
            raise ValueError("The request doesn't contain a url or it's empty")
        self.url = _Token(url)
        self.headers = DictToken(request.get('headers', {}))
        self.body = DictToken(request.get('body', {}))

        method = request.get('method', 'GET')
        if method not in ('GET', 'POST'):
            raise ValueError('Unsupported value for request method: {}'.format(method))
        self.method = _Token(method)

    def render_request(self, context):
        return Request(
            url=self.url.render(context),
            method=self.method.render(context),
            headers=self.headers.render(context),
            body=self.body.render(context)
        )


class CheckpointConfiguration(object):
    def __init__(self, name, content):
        self.name = name
        self.content = content


class BaseTask(object):
    def __init__(self):
        self._pre_process_handler = []
        self._post_process_handler = []
        self._skip_pre_conditions = ConditionGroup()
        self._skip_post_conditions = ConditionGroup()

    def add_preprocess_handler(self, method, input, output):
        """
        Add a preprocess handler. All handlers will be maintained and
        executed sequentially.
        :param method: The method name.
        :type method: ``string``
        :param input: The input of the method.
        :type input: ``list``
        :param output: The output variable name.
        :type output: ``string``
        """
        handler = ProcessHandler(method, input, output)
        self._post_process_handler.append(handler)

    def add_preprocess_skip_condition(self, method, input):
        """
        Add a preprocess skip condition. The skip_conditions for preprocess
        defines a group of conditions and the relation of them is OR which
        means if any one of them returns True then the whole skip_conditions
        returns True. If it returns True, then the preprocess pipeline will
         be skipped.
        :param method: The method name.
        :type method: ``string``
        :param input: The input of the method.
        :type input: ``list``
        """
        self._skip_pre_conditions.add(Condition(method, input))

    def add_postprocess_handler(self, method, input, output):
        """
        Add a postprocess handler. All handlers will be maintained and
        executed sequentially.
        :param method: The method name.
        :type method: ``string``
        :param input: The input of the method.
        :type input: ``list``
        :param output: The output variable name.
        :type output: ``string``
        """
        handler = ProcessHandler(method, input, output)
        self._post_process_handler.append(handler)

    def add_postprocess_skip_condition(self, method, input):
        """
        Add a preprocess skip condition. The skip_conditions for postprocess
        defines a group of conditions and the relation of them is OR which means
         if any one of them returns True then the whole skip_conditions returns
          True. If it returns True, then the postprocess pipeline will be skipped.

        :param method: The method name.
        :type method: ``string``
        :param input: The input of the method.
        :type input: ``list``
        """
        self._skip_post_conditions.add(Condition(method, input))

    def _execute_handlers(self, handlers, context):
        if not handlers:
            logger.debug('No any handler found')
            return
        for handler in handlers:
            try:
                r = handler.execute(context)
            except StopCCEIteration:
                logger.info('Stop task signal received, stop executing handlers')
                break
            else:
                if r:
                    context.update(r)
        logger.debug('Execute handlers finished successfully.')

    def _pre_process(self, context):
        if self._skip_pre_conditions.passed(context):
            logger.debug('Pre process skip condition is passed')
            return
        self._execute_handlers(self._pre_process_handler, context)

    def _post_process(self, context):
        if self._skip_post_conditions.passed(context):
            logger.debug('Post process skip condition is passed')
            return
        self._execute_handlers(self._post_process_handler, context)

    @abstractmethod
    def perform(self, context):
        pass


class CCESplitTask(BaseTask):
    def perform(self, context):
        pass


class CCEHTTPRequestTask(BaseTask):
    """
    CCEHTTPTask represents a HTTP request's properties and its methods.
    It can configure all properties covered by request JSON schema,
     like url, method, auth, pre-process, post-process, skip conditions etc.
    All properties could contain jinja2 template which will be render
     from context when executing.
    """

    def __init__(self, request):
        super(CCEHTTPRequestTask, self).__init__()
        self._request = RequestWithToken(request)
        self._stop_conditions = ConditionGroup()
        self._finished_iter_count = 0
        self._proxy_info = None
        self._iteration_count = None
        self._checkpoint_manager = None  # TODO
        self._checkpoint_conf = None
        self._auth_type = None
        self._auth_settings = None
        self._client = None

    def set_proxy(self, proxy_setting):
        """
        Setup the proxy setting.

        :param proxy_setting: Proxy setting should include the following fields
            "proxy_enabled": ,
            "proxy_url":,
            "proxy_port": ,
            "proxy_username": ,
            "proxy_password": ,
            "proxy_rdns": ,
            "proxy_type": ,
        :type proxy_setting: ``dict``
        """
        self._proxy_info = get_proxy_info(proxy_setting)

    def set_auth(self, auth_type, settings):
        """
        Set the authentication of HTTP request.
        :param auth_type: Authentication type.
        :type auth_type: ``string``
        :param settings: The detail setting of authentication. It
        could contain jinja2
         template. For example:
            {"username": xxx, "password": xxx}
        :type settings: ``dict``
        """
        self._auth_type = auth_type
        self._auth_settings = settings

    def set_iteration_count(self, count):
        """
        Set the maximum loop count for the request. The request will ignore
         this field if it's less or equal to 0 and will not stopped until
          the stop conditions satisfied. Otherwise if the request count
          reaches the iteration_count, the request will stop.
        :param count: Iteration count.
        :type count: ``integer``
        """
        try:
            self._iteration_count = int(count)
        except ValueError:
            raise ValueError('Invalid iteration count: %s' % count)

    def add_stop_condition(self, method, input):
        """
        Add a stop condition. The stop_conditions is a group of conditions
         which defines when the request loop should be stopped and the
         relation of them is OR which means if any one of them returns
         True, then the whole skip_conditions returns True. If it
         returns True, then stop looping the request.
        :param method: The method name.
        :type method: ``string``
        :param input: The input of the method.
        :type input: ``list``
        """
        self._stop_conditions.add(Condition(method, input))

    def configure_checkpoint(self, name, content):
        """
        :param name: The checkpoint name.
        :type name: ``string``
        :param content: The checkpoint content.
        :type content: ``dict``
        """
        if not name or not name.strip():
            raise ValueError('Invalid checkpoint name: "{}"'.format(name))
        if not content:
            raise ValueError('Invalid checkpoint content: {}'.format(content))
        self._checkpoint_conf = CheckpointConfiguration(name.strip(), content)

    def _should_exit(self, context):
        if self._finished_iter_count >= self._iteration_count:
            logger.info('Iteration count reached %s', self._iteration_count)
            return True
        if self._stop_conditions.passed(context):
            logger.info('Stop conditions passed')
            return True

        return False

    def _send_request(self, request):
        try:
            response = self._client.send(request)
        except HTTPError as error:
            logger.exception(
                'Error occurred in request url=%s method=%s reason=%s',
                request.url, request.method, error.reason
            )
            return None, True

        status = response.status_code

        if status in defaults.success_statuses:
            if not (response.body or '').strip():
                logger.info(
                    'The response body of request which url=%s and'
                    ' method=%s is empty, status=%s.',
                    request.url, request.method, status
                )
                return None, True
            return response, False

        error_log = ('The response status=%s for request which url=%s and'
                     ' method=%s.') % (
                        status, request.url, request.method
                    )

        if status in defaults.warning_statuses:
            logger.warning(error_log)
        else:
            logger.error(error_log)

        return None, True

    def _persist_checkpoint(self):
        # TODO storage checkpoint
        pass

    def perform(self, context):
        logger.debug('Start to perform task')

        self._client = HttpClient(self._proxy_info)

        while True:
            self._pre_process(context)

            r = self._request.render_request(context)
            response, need_exit = self._send_request(r)
            if need_exit:
                logger.info('Task need been terminated due to request result')
                break

            context[_RESPONSE_KEY] = response

            self._post_process(context)
            self._persist_checkpoint()
            if self._should_exit(context):
                break

        yield context

        logger.debug('Perform task finished')
