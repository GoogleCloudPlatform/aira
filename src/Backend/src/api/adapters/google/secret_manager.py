"""
Module with the implementation of speech to text
"""
import typing

from google.cloud import secretmanager_v1beta1 as google_sm
from google.oauth2 import service_account

from api import ports


# pylint: disable=too-few-public-methods
class SecretManager(ports.SecretManager):
    """
    Implementation of google's secret manager.
    """

    Secrets: typing.TypeAlias = ports.Secrets

    def __init__(self, project_id: str, creds_path: str):
        credentials = None
        if creds_path:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path
            )
        self.client = google_sm.SecretManagerServiceAsyncClient(credentials=credentials)
        self.project_id = project_id

    async def read(self, secret_id: str) -> Secrets | None:
        """
        Read from the google's secret manager to get the specific secret.
        """
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        request = google_sm.AccessSecretVersionRequest(name=secret_name)
        response = await self.client.access_secret_version(request=request)
        return response.payload.data.decode("utf-8")
