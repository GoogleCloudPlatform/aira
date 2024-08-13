"""
Module with the implementation of speech to text
"""

import datetime
import logging
import os
import typing
import uuid

import ffmpeg
import google.cloud.speech_v2 as speech
from google.api_core import client_options
from google.cloud.speech_v2.types import cloud_speech
from google.oauth2 import service_account

from api import ports
from api.helpers import util

TOTAL_TIME = datetime.timedelta(seconds=61)


logger = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class SpeechToTextV2(ports.SpeechToText):
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
        self.region = "us-central1"
        self.options = client_options.ClientOptions(  # type: ignore[no-untyped-call]
            api_endpoint=f"{self.region}-speech.googleapis.com"
        )
        self.client = speech.SpeechAsyncClient(credentials=self.credentials)
        self.storage: ports.Storage = storage
        self.language = language
        self.project_id = project_id
        self.audio_tmp = "/tmp"
        self.recognizer_name = {
            "latest_long": self._get_recognizer(
                self.credentials, language, model_type="latest_long"
            ),
            "latest_short": self._get_recognizer(
                self.credentials, language, model_type="latest_short"
            ),
        }

    def _get_recognizer(
        self,
        credentials: service_account.Credentials,
        language: str,
        model_type: str = "latest_long",
    ) -> str:
        sync_client = speech.SpeechClient(credentials=credentials)
        list_request = speech.ListRecognizersRequest(
            parent=f"projects/{self.project_id}/locations/global"
        )
        recognizers = sync_client.list_recognizers(request=list_request)
        recognizer: speech.Recognizer
        for recognizer in recognizers:
            if recognizer.model == model_type:
                return recognizer.name

        features = cloud_speech.RecognitionFeatures(
            enable_word_confidence=True,
            enable_word_time_offsets=True,
            max_alternatives=0,
        )
        return self._create_recognizer(
            sync_client, "global", model_type, language, features
        )

    def _create_recognizer(
        self,
        sync_client: speech.SpeechClient,
        region: str,
        model_type: str,
        language: str,
        features: cloud_speech.RecognitionFeatures,
    ) -> str:
        recognizer_data = speech.Recognizer(
            display_name="LIA Recognizer",
            model=model_type,
            language_codes=[language],
            default_recognition_config=cloud_speech.RecognitionConfig(
                features=features,
            ),
        )

        create_request = speech.CreateRecognizerRequest(
            parent=f"projects/{self.project_id}/locations/{region}",
            recognizer=recognizer_data,
            recognizer_id=f"a{uuid.uuid4()}",
        )
        operation = sync_client.create_recognizer(request=create_request)
        recognizer: speech.Recognizer = operation.result()  # type: ignore[no-untyped-call]
        return recognizer.name

    # pylint: disable=too-many-arguments,too-many-locals,too-complex,too-many-nested-blocks
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
        model_type: str = "latest_long",
    ) -> str:
        """
        Run speech to text.
        """
        client = self.client
        recognizer = self.recognizer_name[model_type]
        total_time = datetime.timedelta(seconds=duration)
        config_boosted = cloud_speech.RecognitionConfig(
            explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate if sample_rate else 48000,
                audio_channel_count=channels if channels else 1,
            ),
        )
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=recognizer,
            config=config_boosted,
            files=[cloud_speech.BatchRecognizeFileMetadata(uri=path)],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig()
            ),
        )
        operation = await client.batch_recognize(request=request)
        response: cloud_speech.BatchRecognizeResponse = (
            await operation.result()  # type: ignore[no-untyped-call]
        )
        try:
            transcript_arr: list[str] = []
            last_time = datetime.timedelta(seconds=0)
            i = 1
            if file_result := response.results.get(path):
                transcript_stt = file_result.transcript
                for result in transcript_stt.results:
                    if result.alternatives and (alternative := result.alternatives[0]):
                        for word_obj in alternative.words:
                            start_time = word_obj.start_offset
                            last_time = word_obj.end_offset
                            if (
                                depth < 2
                                and (last_time - start_time).total_seconds() >= 5.0
                            ):
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
        return ""

    async def delete_phrase_set(self, phrase_set_id: str) -> None:
        return

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


class SpeechToTextV2Chirp(ports.SpeechToText):
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
        self.region = "us-central1"
        self.options = client_options.ClientOptions(  # type: ignore[no-untyped-call]
            api_endpoint=f"{self.region}-speech.googleapis.com"
        )
        self.client = speech.SpeechAsyncClient(
            credentials=self.credentials, client_options=self.options
        )
        self.storage: ports.Storage = storage
        self.language = language
        self.project_id = project_id
        self.audio_tmp = "/tmp"
        self.recognizer_name = self._get_recognizer(self.credentials, language)

    def _get_recognizer(
        self, credentials: service_account.Credentials, language: str
    ) -> str:
        sync_client = speech.SpeechClient(
            credentials=credentials, client_options=self.options
        )
        list_request = speech.ListRecognizersRequest(
            parent=f"projects/{self.project_id}/locations/{self.region}"
        )
        recognizers = sync_client.list_recognizers(request=list_request)
        recognizer: speech.Recognizer
        for recognizer in recognizers:
            if recognizer.model == "chirp":
                return recognizer.name

        features = cloud_speech.RecognitionFeatures(
            enable_word_time_offsets=True,
            max_alternatives=0,
        )
        return self._create_recognizer(
            sync_client, self.region, "chirp", language, features
        )

    def _create_recognizer(
        self,
        sync_client: speech.SpeechClient,
        region: str,
        model_type: str,
        language: str,
        features: cloud_speech.RecognitionFeatures,
    ) -> str:
        recognizer_data = speech.Recognizer(
            display_name="LIA Recognizer",
            model=model_type,
            language_codes=[language],
            default_recognition_config=cloud_speech.RecognitionConfig(
                features=features,
            ),
        )

        create_request = speech.CreateRecognizerRequest(
            parent=f"projects/{self.project_id}/locations/{region}",
            recognizer=recognizer_data,
            recognizer_id=f"a{uuid.uuid4()}",
        )
        operation = sync_client.create_recognizer(request=create_request)
        recognizer: speech.Recognizer = operation.result()  # type: ignore[no-untyped-call]
        return recognizer.name

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
        model_type: str = "chirp",
    ) -> str:
        """
        Run speech to text.
        """
        client = self.client
        recognizer = self.recognizer_name
        total_time = datetime.timedelta(seconds=duration)
        config_boosted = cloud_speech.RecognitionConfig(
            explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate if sample_rate else 48000,
                audio_channel_count=channels if channels else 1,
            ),
        )
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=recognizer,
            config=config_boosted,
            files=[cloud_speech.BatchRecognizeFileMetadata(uri=path)],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig()
            ),
        )
        operation = await client.batch_recognize(request=request)
        response: cloud_speech.BatchRecognizeResponse = (
            await operation.result()  # type: ignore[no-untyped-call]
        )
        try:
            transcript_arr: list[str] = []
            last_time = datetime.timedelta(seconds=0)
            i = 1
            if file_result := response.results.get(path):
                transcript_stt = file_result.transcript
                if result := transcript_stt.results[0]:
                    if result.alternatives and (alternative := result.alternatives[0]):
                        for word_obj in alternative.words:
                            start_time = word_obj.start_offset
                            last_time = word_obj.end_offset
                            if (
                                depth < 2
                                and (last_time - start_time).total_seconds() >= 5.0
                            ):
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
        return ""

    async def delete_phrase_set(self, phrase_set_id: str) -> None:
        return

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
