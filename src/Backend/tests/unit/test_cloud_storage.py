"""
Module for tests for cloud storage.
"""

import unittest.mock

import hypothesis
import pytest
from api.adapters.google import CloudStorage
from hypothesis import strategies as st


@hypothesis.given(file_name=st.text())
@pytest.mark.asyncio
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=1,
)
async def test_should_download(file_name: str, cloud_storage: CloudStorage) -> None:
    """
    tests it should download.
    """
    with unittest.mock.patch("builtins.open", unittest.mock.mock_open()):
        resp = await cloud_storage.download("test", file_name)
    assert cloud_storage.client.download_blob_to_file.call_count >= 1
    assert f"{cloud_storage.audio_path}/{file_name}" == resp


@pytest.mark.asyncio
async def test_should_upload_by_text(cloud_storage: CloudStorage) -> None:
    """
    tests it should upload by text.
    """
    file_name = "test-file.csv"
    resp = await cloud_storage.upload_by_text(file_name, b"test")
    blob = cloud_storage.client.bucket.return_value.blob.return_value
    assert blob.upload_from_string.call_count == 1
    assert resp == "test/test"


@pytest.mark.asyncio
async def test_should_upload_by_file_name(cloud_storage: CloudStorage) -> None:
    """
    tests it should upload by file_name.
    """
    file_name = "test-file.csv"
    with unittest.mock.patch("os.remove", unittest.mock.Mock()):
        resp = await cloud_storage.upload_by_file("test", file_name)
    blob = cloud_storage.client.bucket.return_value.blob.return_value
    assert blob.upload_from_filename.call_count == 1
    assert resp == "test/test"
