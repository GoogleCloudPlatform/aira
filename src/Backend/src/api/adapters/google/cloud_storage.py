"""
Module with the implementation of cloud storage
"""

import asyncio
import datetime
import functools
import os

from google.cloud import storage  # type: ignore[attr-defined]
from google.oauth2 import service_account

from api import errors, ports


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
        expected_bucket = self.storage_path.strip()
        expected_prefix = f"gs://{expected_bucket}/"
        if (
            not expected_bucket
            or not uri.startswith(expected_prefix)
            or "\\" in uri
            or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in uri)
        ):
            raise errors.InvalidField("audio")

        object_path = uri[len(expected_prefix) :]
        if not object_path or any(
            seg in {"", ".", ".."} for seg in object_path.split("/")
        ):
            raise errors.InvalidField("audio")

        if (
            not file_name
            or "/" in file_name
            or "\\" in file_name
            or file_name in {".", ".."}
            or os.path.basename(file_name) != file_name
        ):
            raise errors.InvalidField("audio")

        base_dir = os.path.realpath(self.audio_path)
        audio_temp = os.path.realpath(os.path.join(base_dir, file_name))
        if not audio_temp.startswith(base_dir + os.sep):
            raise errors.InvalidField("audio")

        await asyncio.to_thread(
            functools.partial(self._download_sync, uri, audio_temp)
        )
        return audio_temp

    def _download_sync(self, gcs_path: str, audio_temp: str) -> None:
        """
        Download audio from GCS.
        """
        with open(audio_temp, "wb") as file:
            self.client.download_blob_to_file(gcs_path, file)

    async def upload_by_text(
        self, path: str, text: bytes, content_type: str | None = None
    ) -> str:
        """
        Upload audio to GCS by text.
        """
        blob = self.client.bucket(self.storage_path).blob(path)
        if content_type:
            blob.content_type = content_type
        await asyncio.to_thread(
            functools.partial(blob.upload_from_string, text, content_type=content_type)
        )
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

    async def generate_signed_url(
        self, path: str, mimetype: str, method: str = "PUT"
    ) -> str:
        blob = self.client.bucket(self.storage_path).blob(path)
        response: str = await asyncio.to_thread(
            functools.partial(
                blob.generate_signed_url,
                method=method,
                expiration=datetime.timedelta(hours=1),
                version="v4",
                content_type=mimetype if method != "GET" else None,
            )
        )
        return response

    async def get_blob_content_type(self, path: str) -> str | None:
        blob = self.client.bucket(self.storage_path).get_blob(path)
        if blob is None:
            return None
        content_type: str | None = blob.content_type
        return content_type

    async def get_blob_size(self, path: str) -> int | None:
        blob = self.client.bucket(self.storage_path).get_blob(path)
        if blob is None:
            return None
        size: int | None = blob.size
        return size
