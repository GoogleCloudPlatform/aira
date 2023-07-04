"""
Module with the implementation of cloud storage
"""
import asyncio
import datetime
import functools
import os

import google.cloud.storage as storage  # type: ignore[import]
from google.oauth2 import service_account

from api import ports


class CloudStorage(ports.Storage):
    """
    Implementation of google's cloud storage.
    """

    def __init__(self, project_id: str, storage_path: str, creds_path: str):
        credentials = None
        if creds_path:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path
            )
        self.client = storage.Client(project=project_id, credentials=credentials)
        self.storage_path = storage_path
        self.audio_path = "/tmp"

    async def download(self, uri: str, file_name: str) -> str:
        """
        Download audio from GCS.
        """
        file_gcs_path = uri
        audio_temp = f"{self.audio_path}/{file_name}"
        await asyncio.to_thread(
            functools.partial(self._download_sync, file_gcs_path, audio_temp)
        )
        return audio_temp

    def _download_sync(self, gcs_path: str, audio_temp: str) -> None:
        """
        Download audio from GCS.
        """
        with open(audio_temp, "wb") as file:
            self.client.download_blob_to_file(gcs_path, file)

    async def upload_by_text(self, path: str, text: bytes) -> str:
        """
        Upload audio to GCS by text.
        """
        blob = self.client.bucket(self.storage_path).blob(path)
        await asyncio.to_thread(functools.partial(blob.upload_from_string, text))
        return str(blob.id.rsplit("/", 1)[0])

    async def upload_by_file(self, path: str, audio_path: str) -> str:
        """
        Upload audio to GCS by file.
        """
        blob = self.client.bucket(self.storage_path).blob(path)
        await asyncio.to_thread(
            functools.partial(blob.upload_from_filename, audio_path)
        )
        blob_id: str = blob.id
        end_path: str = blob_id.rsplit("/", 1)[0]
        os.remove(audio_path)
        return end_path

    async def generate_signed_url(self, path: str, mimetype: str) -> str:
        blob = self.client.bucket(self.storage_path).blob(path)
        response: str = await asyncio.to_thread(
            functools.partial(
                blob.generate_signed_url,
                method="PUT",
                expiration=datetime.timedelta(hours=1),
                version="v4",
                content_type=mimetype,
            )
        )
        return response

    async def get_blob_content_type(self, path: str) -> str | None:
        blob = self.client.bucket(self.storage_path).get_blob(path)
        content_type: str | None = blob.content_type
        return content_type
