"""
Module for tests for cloud storage.
"""

import unittest.mock
import uuid

import hypothesis
import pytest
from api.adapters.google import CloudStorage, SpeechToText
from hypothesis import strategies as st


@pytest.mark.asyncio
@hypothesis.given(
    phrases_id=st.text(),
    path=st.text(),
    desired=st.text(),
    words=st.lists(st.text(min_size=1)),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=1,
)
async def test_should_process(
    phrases_id: str,
    path: str,
    desired: str,
    words: list[str],
    stt_client: unittest.mock.Mock,
    cloud_storage: CloudStorage,
) -> None:
    """
    tests it should download.
    """
    cloud_stt = SpeechToText("", "..", cloud_storage)
    cloud_stt.client = stt_client
    with (
        unittest.mock.patch("builtins.open", unittest.mock.mock_open()),
        unittest.mock.patch("os.remove", unittest.mock.Mock()),
        unittest.mock.patch("ffmpeg.input", unittest.mock.Mock()),
    ):
        await cloud_stt.process(phrases_id, path, desired, words, 61)
    assert stt_client.long_running_recognize.call_count >= 1


@pytest.mark.asyncio
@hypothesis.given(
    phrase_set_id=st.uuids(),
    phrases=st.lists(st.dictionaries(keys=st.text(), values=st.integers(), max_size=5)),
)
@hypothesis.settings(
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
    max_examples=1,
)
async def test_should_create_phrase_set(
    phrase_set_id: uuid.UUID,
    phrases: list[dict[str, int]],
    stt_client: unittest.mock.Mock,
    cloud_storage: CloudStorage,
) -> None:
    """
    tests it should create phrase_set.
    """
    cloud_stt = SpeechToText("", "..", cloud_storage)
    cloud_stt.client = stt_client
    adaptation_client = unittest.mock.Mock()
    adaptation_client.return_value = unittest.mock.AsyncMock()
    adaptation_client.return_value.create_phrase_set.return_value = unittest.mock.Mock()
    adaptation_client.return_value.create_phrase_set.return_value.name = "test"
    with (
        unittest.mock.patch(
            "google.cloud.speech_v1p1beta1.AdaptationAsyncClient", adaptation_client
        ),
        unittest.mock.patch("uuid.uuid4", unittest.mock.Mock()) as uuid_mock,
    ):
        uuid_mock.return_value = phrase_set_id
        response = await cloud_stt.create_phrase_set(phrases)
    assert response == "test"
    adaptation_client.return_value.create_phrase_set.assert_called_with(
        {
            "parent": "projects//locations/global",
            "phrase_set_id": str(phrase_set_id),
            "phrase_set": {
                "boost": 20,
                "phrases": phrases,
            },
        }
    )
