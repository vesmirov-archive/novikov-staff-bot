import json
import os
from json.decoder import JSONDecodeError
from types import MappingProxyType

import telebot
from dotenv import load_dotenv, dotenv_values

from errors import InvalidConfigurationFileTypeError

load_dotenv('project.env')


class Settings:
    """
    Describes, stores and configures all the project settings.

    :configuration_file_path: - a path to the configuration JSON file, which represents the base project's config.
    :google_secret_file_path: - a path to the Google authentication file
    :telegram_token: - Telegram authentication token
    """

    def __init__(
            self,
            configuration_file_path: str,
            google_secret_file_path: str,
    ):
        self.config = self._setup_config(configuration_file_path)
        self.configuration_file = configuration_file_path
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


class Telegram:
    """
    Describes, stores and configures all the telegram settings.

    :bot_token: - a bot's telegram authentication token
    """

    def __init__(self, bot_token: str):
        self.bot = telebot.TeleBot(bot_token)
        self.main_markup = telebot.types.ReplyKeyboardMarkup(row_width=2)


settings = Settings(
    configuration_file_path=os.getenv('CONFIGURATION_FILE_PATH'),
    google_secret_file_path=os.getenv('GOOGLE_SECRET_FILE'),
)
telegram = Telegram(
    bot_token=os.getenv('TELEGRAM_TOKEN'),
)
