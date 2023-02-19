from json.decoder import JSONDecodeError

import pygsheets
from pygsheets.client import Client

from errors import InvalidGoogleServiceFileTypeError
from settings import settings


class GoogleManager:
    """
    Contains Google API settings and instances.

    :service_account_file: - a path to the Google service account JSON file.
    """

    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.client = self.get_client()

    def get_client(self) -> Client:
        try:
            client = pygsheets.authorize(service_account_file=self.service_account_file)
        except JSONDecodeError:
            raise InvalidGoogleServiceFileTypeError
        else:
            return client


manager = GoogleManager(settings.google_secret_file)
