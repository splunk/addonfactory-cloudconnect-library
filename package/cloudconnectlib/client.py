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

    def _load_config(self):
        """Load a JSON based configuration definition from file.
        :return: A `dict` contains user defined JSON interface.
        """
        try:
            df = load_json_file(self._config_file)
        except:
            raise ConfigException(
                'Cannot load JSON config from file {}: {}'.format(
                    self._config_file, traceback.format_exc()))

        version = df.get('meta', {'version', None}).get('version', None)
        if not version:
            raise ConfigException(
                'Config meta or version not present in {}'.format(
                    self._config_file))

        config_loader = loader_from_version(version)
        return config_loader.load(df, self._context)

    def start(self):
        """
        Initialize a new `CloudConnectEngine` instance and start it.
        """
        if self._config is None:
            self._config = self._load_config()

        self._engine = CloudConnectEngine()
        self._engine.start(
            context=copy.deepcopy(self._context), config=self._config
        )

    def stop(self):
        """Stop the current cloud connect engine.
        """
        if self._engine:
            self._engine.stop()
