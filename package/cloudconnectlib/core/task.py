from abc import abstractmethod

from cloudconnectlib.common.log import get_cc_logger
from cloudconnectlib.core.http import get_proxy_info

logger = get_cc_logger()


class ProcessHandler(object):
    def __init__(self, method, arguments, output):
        self.method = method
        self.arguments = arguments
        self.output = output


class Condition(object):
    def __init__(self, method, arguments):
        self.method = method
        self.arguments = arguments

    def passed(self, context):
        # TODO check if condition is passed
        return True


class ConditionGroup(object):
    def __init__(self):
        self._conditions = []

    def add(self, condition):
        self._conditions.append(condition)

    def passed(self, context):
        return any(
            cdn.passed(context) for cdn in self._conditions
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
        pass

    def _pre_process(self, context):
        if self._skip_pre_conditions.passed(context):
            logger.debug('Pre process skip condition is passed')
            return
        self._execute_handlers(self._pre_process_handler, context)
        return context

    def _post_process(self, context):
        if self._skip_post_conditions.passed(context):
            logger.debug('Pre process skip condition is passed')
            return
        self._execute_handlers(self._post_process_handler, context)
        return context

    @abstractmethod
    def perform(self):
        pass


class CCESplitTask(BaseTask):
    def perform(self):
        pass


class CCEHTTPRequestTask(BaseTask):
    """
    CCEHTTPTask represents a HTTP request's properties and its methods.
    It can configure all properties covered by request JSON schema,
     like url, method, auth, pre-process, post-process, skip conditions etc.
    All properties could contain jinja2 template which will be render
     from context when executing.
    """

    def __init__(self):
        super(CCEHTTPRequestTask, self).__init__()
        self._proxy_info = None
        self._iteration_count = None
        self._stop_conditions = ConditionGroup()
        self._checkpoint_conf = None
        self._auth_type = None
        self._auth_settings = None
        self._finished_iter_count = 0

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

    def _send_request(self):
        # TODO send request
        pass

    def _persist_checkpoint(self):
        # TODO storage checkpoint
        pass

    def perform(self):
        logger.debug('Start to perform task')

        context = {}
        while True:
            self._pre_process(context)
            self._send_request()
            self._post_process(context)
            self._persist_checkpoint()
            if self._should_exit(context):
                break

        logger.debug('Perform task finished')
