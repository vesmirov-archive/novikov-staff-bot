import json
import os
from json.decoder import JSONDecodeError
from types import MappingProxyType

from dotenv import load_dotenv, dotenv_values
from errors import InvalidConfigurationFileTypeError

load_dotenv('dev.env')

CONFIGURATION_FILE_PATH = os.getenv('CONFIGURATION_FILE_PATH')
ENVIRONMENT_FILE_PATH = os.getenv('ENVIRONMENT_FILE_PATH')
GOOGLE_SECRET_FILE = os.getenv('GOOGLE_SECRET_FILE')


class Settings:
    """
    Describes, stores and configures all the project settings.

    :configuration_file_path: - a path to the configuration JSON file, which represents the base project's config.
    """

    def __init__(
            self,
            configuration_file_path: str,
            environment_file_path: str,
            google_secret_file_path: str,
    ):
        self.config = self._setup_config(configuration_file_path)
        self.environments = self._setup_environments(environment_file_path)
        self.configuration_file = configuration_file_path
        self.environment_file = environment_file_path
        self.google_secret_file = google_secret_file_path

    def __map_dictionary(self, object) -> MappingProxyType:
        """Protects extracted dictionary from editing"""

        if isinstance(object, dict):
            for key in object:
                object[key] = self.__map_dictionary(object[key])
            return MappingProxyType(object)
        elif isinstance(object, list):
            for idx, item in enumerate(object):
                object[idx] = self.__map_dictionary(item)
        return object

    def _setup_config(self, configuration_file_path) -> MappingProxyType:
        try:
            with open(configuration_file_path, 'r') as file:
                raw_config = json.loads(file.read())
        except JSONDecodeError:
            raise InvalidConfigurationFileTypeError
        else:
            return self.__map_dictionary(raw_config)

    def _setup_environments(self, environment_file_path) -> MappingProxyType:
        environment_variables = dotenv_values(environment_file_path)
        return self.__map_dictionary(environment_variables)


settings = Settings(CONFIGURATION_FILE_PATH, ENVIRONMENT_FILE_PATH, GOOGLE_SECRET_FILE)
