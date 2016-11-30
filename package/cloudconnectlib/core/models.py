from abc import abstractmethod


class BaseObject(object):
    @abstractmethod
    def validate(self):
        pass


class Meta(BaseObject):
    """
    A entity class to hold metadata information for JSON interface.
    """

    def __init__(self, meta):
        super(Meta, self).__init__()
        if not isinstance(meta, dict):
            raise ValueError('meta expect be dict')
        self.version = meta['version']

    def validate(self):
        pass


class Proxy(BaseObject):
    """
    A entity class to hold proxy related setting.
    """

    def __init__(self, proxy):
        super(Proxy, self).__init__()
        if not proxy:
            raise ValueError('proxy expect be not None')
        if not isinstance(proxy, dict):
            raise TypeError('proxy expect be a dict')
        self.enabled = proxy.get('enabled', False)
        self.host = proxy['host']
        self.port = proxy['port']
        self.username = proxy.get('username')
        self.password = proxy.get('password')
        self.type = proxy.get('type')
        self.rdns = proxy.get('rdns')

    def validate(self):
        pass


class GlobalSetting(BaseObject):
    """
    A entity class to hold global static settings includes logging and proxy.
    """

    def __init__(self, global_setting):
        super(GlobalSetting, self).__init__()
        if not global_setting:
            raise ValueError('global setting expect be not None')
        if not isinstance(global_setting, dict):
            raise TypeError('global setting expect be a dict')
        self.proxy = Proxy(global_setting['proxy'])
        self.logging = Logging(global_setting['logging']) \
            if 'logging' in global_setting else None

    def validate(self):
        pass


class Function(BaseObject):
    """
    A class represents a handle logic which contains a input, a method and
     a optional output.
    """

    def __init__(self, func):
        super(Function, self).__init__()
        if not func:
            raise ValueError('function expect be not None')
        if not isinstance(func, dict):
            raise TypeError('function expect be a dict')
        self.input = func['input']
        self.method = func['method']
        self.output = func.get('output')

    def validate(self):
        pass


class Logging(BaseObject):
    """
    A entity class to hold logging setting, only logging level now.
    """

    def __init__(self, logging):
        super(Logging, self).__init__()
        if not logging:
            raise ValueError('checkpoint expect be not None')
        if not isinstance(logging, dict):
            raise TypeError('checkpoint expect be a dict')
        self.level = logging['level']

    def validate(self):
        pass


class RequestOption(BaseObject):
    def __init__(self, options):
        super(RequestOption, self).__init__()
        if not options:
            raise ValueError('checkpoint expect be not None')
        if not isinstance(options, dict):
            raise TypeError('checkpoint expect be a dict')
        self.url = options['url']
        self.method = options.get('method', 'GET')
        self.headers = options.get('headers')

    def validate(self):
        pass


class BeforeRequest(BaseObject):
    def __init__(self, br):
        super(BeforeRequest, self).__init__()
        if not br:
            raise ValueError('before request expect be not None')
        if not isinstance(br, list):
            raise TypeError('before request expect be a list')
        self.funcs = [Function(f) for f in br]

    def validate(self):
        pass


class SkipAfterRequest(BaseObject):
    """
    A class to hold a group conditions which used to determine if request need
    to skip the after_request.
    """

    def __init__(self, sar):
        super(SkipAfterRequest, self).__init__()
        if not sar:
            raise ValueError('skip after request expect be not None')
        if not isinstance(sar, dict):
            raise TypeError('skip after request expect be a dict')
        self.conditions = [Function(f) for f in sar.get('conditions', [])]

    def validate(self):
        super(SkipAfterRequest, self).validate()


class AfterRequest(BaseObject):
    """
    A class to hold business logic need to process after the request finished.
    """

    def __init__(self, ar):
        super(AfterRequest, self).__init__()
        if not ar:
            raise ValueError('after request expect be not None')
        if not isinstance(ar, list):
            raise TypeError('after request expect be a list')
        self.funcs = [Function(f) for f in ar]

    def validate(self):
        pass


class LoopMode(BaseObject):
    def __init__(self, lm):
        super(LoopMode, self).__init__()
        if not lm:
            raise ValueError('loop mode expect be not None')
        if not isinstance(lm, dict):
            raise TypeError('loop mode expect be a dict')
        self.type = lm['type']
        self.stop_conditions = lm['stop_conditions']

    def validate(self):
        pass


class Checkpoint(BaseObject):
    """
    A entity class to hold checkpoint settings which contains a namespace and
    the checkpoint content to store.
    """

    def __init__(self, ckpt):
        super(Checkpoint, self).__init__()
        if not ckpt:
            raise ValueError('checkpoint expect be not None')
        if not isinstance(ckpt, dict):
            raise TypeError('checkpoint expect be a dict')
        self.namespace = ckpt['namespace']
        self.content = ckpt['content']

    def validate(self):
        pass


class Request(BaseObject):
    def __init__(self, request):
        super(Request, self).__init__()
        if not request:
            raise ValueError('request expect be not None')
        if not isinstance(request, dict):
            raise TypeError('request expect be a dict')
        self.options = RequestOption(request['options'])
        self.before_request = BeforeRequest(request['before_request'])
        self.skip_after_request = SkipAfterRequest(request['skip_after_request'])
        self.after_request = AfterRequest(request['after_request'])
        self.loop_mode = LoopMode(request['loop_mode'])
        self.checkpoint = Checkpoint(request['checkpoint'])

    def validate(self):
        pass
