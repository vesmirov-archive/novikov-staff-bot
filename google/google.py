import pygsheets
from pygsheets.client import Client

from settings import settings


class Google:
    """
    Contains Google API settings and instances.

    :service_account_file: - a path to the Google service account JSON file.
    """

    def __init__(self, service_account_file: str):
        self.service_account_file = service_account_file
        self.manager = self.get_manager()

    def get_manager(self) -> Client:
        return pygsheets.authorize(service_account_file=self.service_account_file)


google = Google(settings.google_secret_file)