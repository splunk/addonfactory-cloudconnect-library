import json
import threading
from abc import abstractmethod

from cloudconnectlib.common.log import get_cc_logger
from cloudconnectlib.core import defaults
from cloudconnectlib.core.exceptions import HTTPError
from cloudconnectlib.core.exceptions import StopCCEIteration
from cloudconnectlib.core.ext import lookup_method
from cloudconnectlib.core.http import get_proxy_info, HttpClient
from cloudconnectlib.core.models import DictToken, _Token, BasicAuthorization

logger = get_cc_logger()

_RESPONSE_KEY = '__response__'
_AUTH_TYPES = {
    'basic_auth': BasicAuthorization
}


class ProcessHandler(object):
    def __init__(self, method, arguments, output):
        self.method = method
        self.callable_method = lookup_method(method)
        self.arguments = [_Token(arg) for arg in arguments or ()]
        self.output = output

    def execute(self, context):
        args = [arg.render(context) for arg in self.arguments]
        logger.debug('%s arguments found for method %s', len(args), self.method)
        result = self.callable_method(*args)

        data = {}
        if self.output:
            data[self.output] = result

        return data


class Condition(object):
    def __init__(self, method, arguments):
        self.method = method
        self.callable_method = lookup_method(method)
        self.arguments = [_Token(arg) for arg in arguments or ()]

    def is_meet(self, context):
        args = [arg.render(context) for arg in self.arguments]
        logger.debug('%s arguments found for method %s', len(args), self.method)
        return self.callable_method(args)


class ConditionGroup(object):
    def __init__(self):
        self._conditions = []

    def add(self, condition):
        self._conditions.append(condition)

    def is_meet(self, context):
        return any(
            cdn.is_meet(context) for cdn in self._conditions
        )


class ProxyTemplate(object):
    def __init__(self, proxy_setting):
        if not proxy_setting:
            raise ValueError('Invalid proxy setting: {}'.format(proxy_setting))
        self._enabled = _Token(proxy_setting.get('proxy_enabled', ''))

        url, port = proxy_setting.get('proxy_url'), proxy_setting.get('proxy_port')
        if not all((url, port)):
            raise ValueError('Invalid proxy url={} or port={}'.format(url, port))
        self._url = _Token(url)
        self._port = _Token(port)

        self._rdns = _Token(proxy_setting.get('proxy_rdns', ''))
        self._user = _Token(proxy_setting.get('proxy_username', ''))
        self._password = _Token(proxy_setting.get('proxy_password', ''))
        self._proxy_type = _Token(proxy_setting.get('proxy_type', 'http'))

    def render(self, context):
        rendered_conf = {
            'proxy_enabled': self._enabled.render(context),
            'proxy_type': self._proxy_type.render(context),
            'proxy_url': self._url.render(context),
            'proxy_port': self._port.render(context),
            'proxy_username': self._user.render(context),
            'proxy_password': self._password.render(context),
            'proxy_rdns': self._rdns.render(context)
        }
        return get_proxy_info(rendered_conf)


class Request(object):
    def __init__(self, method, url, headers, body):
        self.method = method
        self.url = url
        self.headers = headers
        if not body:
            self.body = None
        elif not isinstance(body, basestring):
            self.body = json.dumps(body)
        else:
            self.body = body


class RequestTemplate(object):
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
        if not method or method.upper() not in ('GET', 'POST'):
            raise ValueError('Unsupported value for request method: {}'.format(method))
        self.method = _Token(method)

    def render(self, context):
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
    def __init__(self, name):
        self._name = name
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

    @staticmethod
    def _execute_handlers(skip_conditions, handlers, context, phase):
        if skip_conditions.is_meet(context):
            logger.debug('%s skip conditions are met', phase.capitalize())
            return
        if not handlers:
            logger.debug('No handler found in %s', phase)
            return

        for handler in handlers:
            try:
                data = handler.execute(context)
            except StopCCEIteration:
                logger.info('Stop task signal received, stop executing handlers')
                break
            else:
                if data:
                    # FIXME
                    context.update(data)
        logger.debug('Execute handlers finished successfully.')

    def _pre_process(self, context):
        self._execute_handlers(self._skip_pre_conditions,
                               self._pre_process_handler,
                               context, 'pre process')

    def _post_process(self, context):
        self._execute_handlers(self._skip_post_conditions,
                               self._post_process_handler,
                               context, 'post process')

    @abstractmethod
    def perform(self, context):
        pass

    def stop(self, block=False, timeout=30):
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

    def __init__(self, request, name, conf=None):
        super(CCEHTTPRequestTask, self).__init__(name)
        self._request = RequestTemplate(request)
        self._conf = conf
        self._stop_conditions = ConditionGroup()
        self._finished_iter_count = defaults.max_iteration_count
        self._proxy_info = None
        self._iteration_count = 0
        self._checkpoint_manager = None  # TODO
        self._checkpoint_conf = None
        self._http_client = None
        self._authorizer = None
        self._stopped = threading.Event()
        self._stop_signal_received = False

    def stop(self, block=False, timeout=30):
        """
        Stop current task.
        """
        if self._stopped.is_set():
            logger.info('Task is not running, cannot stop it.')
            return
        self._stop_signal_received = True

        if not block:
            return

        if not self._stopped.wait(timeout):
            logger.info('Waiting for stop task timeout')

    def _check_if_stop_needed(self):
        if self._stop_signal_received:
            logger.info('Stop task signal received, stopping task.')
            self._stopped.set()
            return True
        return False

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
        self._proxy_info = ProxyTemplate(proxy_setting)

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
        if not auth_type:
            raise ValueError('Invalid auth type={}'.format(auth_type))
        authorizer_cls = _AUTH_TYPES.get(auth_type.lower())
        if not authorizer_cls:
            raise ValueError('Unsupported auth type={}'.format(auth_type))
        self._authorizer = authorizer_cls(settings)

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
            self._iteration_count = defaults.max_iteration_count
            logger.warning(
                'Invalid iteration count: %s, using default max iteration count: %s',
                count, self._iteration_count)

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
        if 0 < self._iteration_count <= self._finished_iter_count:
            logger.info('Iteration count reached %s', self._iteration_count)
            return True
        if self._stop_conditions.is_meet(context):
            logger.info('Stop conditions are met')
            return True
        return False

    def _send_request(self, request, proxy_info=None):
        try:
            response = self._http_client.send(request, proxy_info)
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
        if not self._checkpoint_manager:
            logger.info('Checkpoint is not configured. Skip persist checkpoint.')
            # TODO

    def perform(self, context):
        logger.debug('Start to perform task')

        self._http_client = HttpClient()

        while True:
            self._pre_process(context)

            if self._check_if_stop_needed():
                break

            r = self._request.render(context)
            if self._authorizer:
                self._authorizer(r.headers, context)

            proxy_info = self._proxy_info.render(context) if self._proxy_info else None
            response, need_exit = self._send_request(r, proxy_info)
            if need_exit:
                logger.info('Task need been terminated due to request result')
                break
            if self._check_if_stop_needed():
                break

            context[_RESPONSE_KEY] = response

            self._post_process(context)
            self._persist_checkpoint()

            if self._check_if_stop_needed():
                break

            self._finished_iter_count += 1
            if self._should_exit(context):
                break

        yield context

        self._stopped.set()
        logger.debug('Perform task finished')

    def __str__(self):
        return self._name

    def __repr__(self):
        return self.__str__()
