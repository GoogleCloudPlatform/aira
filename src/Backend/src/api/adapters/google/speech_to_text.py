"""
Module with the implementation of speech to text
"""

import datetime
import logging
import os
import typing
import uuid

import ffmpeg
import google.cloud.speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1.types import cloud_speech
from google.oauth2 import service_account

from api import ports
from api.helpers import util

logger = logging.getLogger(__name__)


class SpeechToText(ports.SpeechToText):
    """
    Implementation of google's speech to text.
    """

    def __init__(
        self,
        project_id: str,
        creds_path: str,
        storage: ports.Storage,
        language: str = "pt-BR",
    ):
        self.credentials = None
        if creds_path:
            self.credentials = service_account.Credentials.from_service_account_file(
                creds_path
            )
        self.client = speech.SpeechAsyncClient(credentials=self.credentials)
        self.storage: ports.Storage = storage
        self.project_id = project_id
        self.audio_tmp = "/tmp"
        self.language = language

    async def process(
        self,
        phrases_id: str,
        path: str,
        desired: str,
        words: list[str],
        duration: int,
        depth: int = 0,
        sample_rate: int | None = None,
        channels: int | None = None,
        model_type: str = "latest_short",
    ) -> str:
        """
        Run speech to text.
        """
        total_time = datetime.timedelta(seconds=duration)
        speech_adaptation = None
        if phrases_id:
            parent = (
                f"projects/{self.project_id}/locations/global/phraseSets/{phrases_id}"
            )
            speech_adaptation = speech.SpeechAdaptation(phrase_set_references=[parent])

        metadata = speech.RecognitionMetadata()
        metadata.interaction_type = (
            speech.RecognitionMetadata.InteractionType.DICTATION  # type: ignore
        )
        metadata.original_media_type = (
            speech.RecognitionMetadata.OriginalMediaType.AUDIO  # type: ignore
        )

        config_boosted = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate if sample_rate else 48000,
            audio_channel_count=channels if channels else 1,
            language_code=self.language,
            adaptation=speech_adaptation,
            model=model_type,
            enable_word_confidence=True,
            enable_word_time_offsets=True,
            metadata=metadata,
        )

        aud = speech.RecognitionAudio(uri=path)
        operation = await self.client.long_running_recognize(
            config=config_boosted, audio=aud
        )
        response = await operation.result()  # type: ignore[no-untyped-call]
        try:
            transcript_arr = []
            last_time: datetime.timedelta = datetime.timedelta(seconds=0)
            i = 1
            if response.results:
                result = response.results[0]
                word_obj: cloud_speech.WordInfo
                for word_obj in result.alternatives[0].words:
                    start_time = word_obj.start_time
                    last_time = word_obj.end_time
                    if depth < 2 and (last_time - start_time).total_seconds() >= 5.0:
                        new_transcript = await self._rerun_audio(
                            path=path,
                            desired=desired,
                            start_time=start_time,
                            last_time=last_time,
                            phrases=phrases_id,
                            words=words,
                            duration=duration,
                            i=i,
                            depth=depth + 1,
                            sample_rate=sample_rate,
                            channels=channels,
                        )
                        transcript_arr.extend(new_transcript.split(" "))
                        i += 1
                    else:
                        word_data = word_obj.word
                        transcript_arr.extend(
                            util.convert_number_to_written_text(
                                word_data, self.language
                            )
                            if word_data.isdecimal()
                            else [word_data]
                        )
                if depth < 2 and (total_time - last_time).total_seconds() >= 5.0:
                    new_transcript = await self._rerun_audio(
                        path,
                        desired,
                        start_time=last_time,
                        last_time=total_time,
                        phrases=phrases_id,
                        words=words,
                        duration=duration,
                        i=i,
                        depth=depth + 1,
                        sample_rate=sample_rate,
                        channels=channels,
                    )
                    transcript_arr.extend(new_transcript.split(" "))
            result_transc = " ".join(transcript_arr)
        except IndexError:
            return ""
        return result_transc

    async def create_phrase_set(self, phrases: list[dict[str, typing.Any]]) -> str:
        """
        Method to build phrase set that will be used as context.
        """
        parent = f"projects/{self.project_id}/locations/global"
        adaptation_client = speech.AdaptationAsyncClient(credentials=self.credentials)
        phrase_set_response = await adaptation_client.create_phrase_set(
            {
                "parent": parent,
                "phrase_set_id": str(uuid.uuid4()),
                "phrase_set": {
                    "boost": 20,
                    "phrases": phrases,
                },
            }
        )
        return phrase_set_response.name

    # pylint: disable=too-many-arguments
    async def _rerun_audio(
        self,
        path: str,
        desired: str,
        start_time: datetime.timedelta,
        last_time: datetime.timedelta,
        phrases: str,
        words: list[str],
        duration: int,
        i: int,
        depth: int,
        sample_rate: int | None = None,
        channels: int | None = None,
    ) -> str:
        """
        Method to rerun portion of audio.
        """
        temp_path = await self.storage.download(path, desired)
        temp_path = await self._cut_audio(
            temp_path, desired, start_time.total_seconds(), last_time.total_seconds()
        )
        desired_name = f"{desired.replace('.wav', '')}-{i}.wav"

        new_uri = await self.storage.upload_by_file(f"cutted/{desired_name}", temp_path)
        process_result = await self.process(
            phrases_id=phrases,
            path=f"gs://{new_uri}",
            desired=desired,
            words=words,
            duration=duration,
            depth=depth,
            sample_rate=sample_rate,
            channels=channels,
            model_type="latest_short",
        )
        return process_result

    async def _cut_audio(
        self, audio_path: str, file_name: str, start_time: float, end_time: float
    ) -> str:
        """
        Cut portion of the audio.
        """
        audio_cutted = f"/{self.audio_tmp}/cutted_{file_name}"
        ffmpeg.input(audio_path).output(
            audio_cutted, **{"ss": start_time, "to": end_time}
        ).run(overwrite_output=True, quiet=True)
        os.remove(audio_path)
        return audio_cutted

    async def delete_phrase_set(self, phrase_set_id: str) -> None:
        parent = (
            f"projects/{self.project_id}/locations/global/phraseSets/{phrase_set_id}"
        )
        adaptation_client = speech.AdaptationAsyncClient(credentials=self.credentials)
        await adaptation_client.delete_phrase_set(name=parent)
