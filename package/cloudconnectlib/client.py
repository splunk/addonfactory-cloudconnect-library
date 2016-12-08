import copy
import traceback

from .configuration import loader_from_version
from .core import CloudConnectEngine
from .core.exceptions import ConfigException
from .core.util import load_json_file


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

    def _lazy_load_config(self):
        """Load a JSON based configuration definition from file.
        :return: A `dict` contains user defined JSON interface.
        """
        try:
            df = load_json_file(self._config_file)
        except:
            raise ConfigException(
                'Cannot load JSON config from file {}: {}'.format(
                    self._config_file, traceback.format_exc()))

        try:
            version = df['meta']['version']
        except KeyError:
            raise ConfigException(
                'Config version not present in {}'.format(self._config_file))

        config_loader = loader_from_version(version)
        return config_loader.load(df, self._context)

    def start(self):
        """
        Initialize a new `CloudConnectEngine` instance and start it.
        """
        if self._config is None:
            self._config = self._lazy_load_config()

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
