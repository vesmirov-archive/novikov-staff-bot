import json
import os
from json.decoder import JSONDecodeError
from types import MappingProxyType

from dotenv import load_dotenv

from errors import InvalidConfigurationFileTypeError

load_dotenv('dev.env')

CONFIGURATION_FILE_PATH = os.getenv('CONFIGURATION_FILE_PATH')


class Settings:
    """
    Describes, stores and configures all the project settings.

    :configuration_file_path: - the path to the configuration JSON file,
                                which represents the base project's config.
    """

    def __init__(self, configuration_file_path):
        self.config = self._setup_config(configuration_file_path)

    def __map_dictionary(self, object):
        """Protects extracted config dictionary from editing"""

        if isinstance(object, dict):
            for key in object:
                object[key] = self.__map_dictionary(object[key])
            return MappingProxyType(object)
        elif isinstance(object, list):
            for idx, item in enumerate(object):
                object[idx] = self.__map_dictionary(item)
        return object

    def _setup_config(self, path: str):
        try:
            with open(path, 'r') as file:
                raw_config = json.loads(file.read())
        except JSONDecodeError:
            raise InvalidConfigurationFileTypeError
        else:
            return self.__map_dictionary(raw_config)


settings = Settings(CONFIGURATION_FILE_PATH)
