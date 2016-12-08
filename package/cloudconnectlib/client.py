import copy

from .configuration import CloudConnectConfigLoaderV1
from .core import CloudConnectEngine


class CloudConnectClient(object):
    """
    The client of cloud connect used to start a cloud connect engine instance.
    """

    def __init__(self, context, config_file):
        """
        Constructs a `CloudConnectClient` with `context` which contains variables
        to render template in the configuration parsed from file `config_file`.
        :param context: context to render template.
        :param config_file: file path for load user passed interface.
        """
        self._context = context
        self._config_file = config_file
        self._engine = None
        self._config = None

    def start(self):
        """
        Initialize a new `CloudConnectEngine` instance and start it.
        """
        if self._config is None:
            config_loader_v1 = CloudConnectConfigLoaderV1()
            self._config = config_loader_v1.load(
                file_path=self._config_file,
                context=self._context
            )
        self._engine = CloudConnectEngine(
            context=copy.deepcopy(self._context), config=self._config
        )
        self._engine.start()

    def stop(self):
        """
        Stop the current cloud connect engine.
        """
        if self._engine:
            self._engine.stop()
