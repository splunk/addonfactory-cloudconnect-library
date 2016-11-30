class TokenizedObject(object):
    def __init__(self, template):
        self._template = template

    def value(self):
        return self._template


class Request(object):
    def __init__(self):
        pass

class Header(object):
    def __init__(self):
        self._items = dict()

    def add(self, key, value):
        self._items.update({key:TokenizedObject(value)})

class Options(object):
    def __init__(self, headers, url ,method):
        self._headers = headers
        self._url = TokenizedObject(url)
        self._method = method

class ProcessHandler(object):
    def __init__(self, inputs, func, output):
        pass

class BeforeRequest(ProcessHandler):
    pass

class AfterRequest(ProcessHandler):
    pass

class Condition(ProcessHandler):
    pass

class SkipAfterRequest(object):
    def __init__(self):
        self._conditions = []

    def addcondition(self, condition):
        self._conditions.append(condition)


class LoopMode(object):
    def __init__(self, type):
        self._type = type
        self._conditions = []

class Checkpoint(object):
    def __init__(self):
        self._namespace= []
        self._content = dict()

