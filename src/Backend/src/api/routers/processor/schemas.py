"""
Module that contains all schemas to the processor endpoint.
"""

import dataclasses
import enum
import typing
import uuid

import pydantic

from api import models, typings
from api.helpers import schemas

# pylint: disable=too-few-public-methods


class AudioFileType(enum.StrEnum):
    """Allowed file extensions for exam audio signed uploads."""

    WAV = "wav"
    OGG = "ogg"
    WEBM = "webm"
    MP3 = "mp3"


class AudioMimeType(enum.StrEnum):
    """Allowed audio/* MIME types for exam audio signed uploads."""

    AUDIO_WAV = "audio/wav"
    AUDIO_X_WAV = "audio/x-wav"
    AUDIO_OGG = "audio/ogg"
    AUDIO_WEBM = "audio/webm"
    AUDIO_MPEG = "audio/mpeg"
    AUDIO_MP3 = "audio/mp3"


ALLOWED_AUDIO_MIME_TYPES: dict[AudioFileType, frozenset[AudioMimeType]] = {
    AudioFileType.WAV: frozenset({AudioMimeType.AUDIO_WAV, AudioMimeType.AUDIO_X_WAV}),
    AudioFileType.OGG: frozenset({AudioMimeType.AUDIO_OGG}),
    AudioFileType.WEBM: frozenset({AudioMimeType.AUDIO_WEBM}),
    AudioFileType.MP3: frozenset({AudioMimeType.AUDIO_MPEG, AudioMimeType.AUDIO_MP3}),
}


class ImportFileType(enum.StrEnum):
    """Allowed file extensions for admin bulk-import signed uploads."""

    CSV = "csv"


class ImportMimeType(enum.StrEnum):
    """Allowed MIME types for admin bulk-import signed uploads."""

    TEXT_CSV = "text/csv"


ALLOWED_IMPORT_MIME_TYPES: dict[ImportFileType, frozenset[ImportMimeType]] = {
    ImportFileType.CSV: frozenset({ImportMimeType.TEXT_CSV}),
}


def _reject_unsafe_chars(value: object, *, allow_slash: bool) -> object:
    if not isinstance(value, str):
        raise ValueError("Value must be a string.")
    if (
        ".." in value
        or "\\" in value
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)
    ):
        raise ValueError("Value contains forbidden path or control characters.")
    if not allow_slash and "/" in value:
        raise ValueError("Value must not contain '/'.")
    return value


class PubsubData(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines only needed data that will be converted from pubsub.
    """

    result_id: uuid.UUID
    phrase_set_id: str
    audio: str
    words: list[str]
    question_type: str | None
    question_theme: str | None


class PubsubDataReprocessed(PubsubData):
    """
    Defines only needed data that will be converted from pubsub.
    """

    duration: int
    sample_rate: int | None
    channels: int | None


class CreateSignedRequest(pydantic.BaseModel):
    """
    Defines the base configuration for signed-upload requests.
    """

    class Config:
        extra = pydantic.Extra.forbid


class CreateUserSignedRequest(CreateSignedRequest):
    """
    Defines the needed data to create a signed url for student/teacher audio uploads.
    """

    file_type: AudioFileType
    mimetype: AudioMimeType
    exam_id: uuid.UUID
    question_id: uuid.UUID
    user_id: uuid.UUID

    @pydantic.validator("file_type", pre=True)
    @classmethod
    def validate_file_type_chars(cls, value: object) -> object:
        return _reject_unsafe_chars(value, allow_slash=False)

    @pydantic.validator("mimetype", pre=True)
    @classmethod
    def validate_mimetype_chars(cls, value: object) -> object:
        return _reject_unsafe_chars(value, allow_slash=True)

    @pydantic.root_validator
    @classmethod
    def validate_audio_pair(
        cls, values: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        file_type = values.get("file_type")
        mimetype = values.get("mimetype")
        if file_type is not None and mimetype is not None:
            allowed = ALLOWED_AUDIO_MIME_TYPES.get(file_type, frozenset())
            if mimetype not in allowed:
                raise ValueError("mimetype does not match file_type.")
        return values


class CreateImportSignedRequest(CreateSignedRequest):
    """
    Defines the needed data to create a signed url for admin CSV imports.
    """

    file_type: ImportFileType
    mimetype: ImportMimeType
    type: schemas.ImportType

    @pydantic.validator("file_type", pre=True)
    @classmethod
    def validate_file_type_chars(cls, value: object) -> object:
        return _reject_unsafe_chars(value, allow_slash=False)

    @pydantic.validator("mimetype", pre=True)
    @classmethod
    def validate_mimetype_chars(cls, value: object) -> object:
        return _reject_unsafe_chars(value, allow_slash=True)

    @pydantic.root_validator
    @classmethod
    def validate_import_pair(
        cls, values: dict[str, typing.Any]
    ) -> dict[str, typing.Any]:
        file_type = values.get("file_type")
        mimetype = values.get("mimetype")
        if file_type is not None and mimetype is not None:
            allowed = ALLOWED_IMPORT_MIME_TYPES.get(file_type, frozenset())
            if mimetype not in allowed:
                raise ValueError("mimetype does not match file_type.")
        return values


class SignedUrl(pydantic.BaseModel):
    """
    Signed url response
    """

    signed_url: pydantic.AnyHttpUrl


@dataclasses.dataclass
class ReprocessedMessage(typings.Message):
    """
    Dataclass for message sent to pubsub
    """

    result_id: uuid.UUID
    words: list[str]
    phrase_set_id: str
    audio: str
    duration: int
    sample_rate: int | None
    channels: int | None
    question_type: str | None
    question_theme: str | None


class GenerateWord(pydantic.BaseModel):
    """
    Defines the needed data to generate readable words
    """

    qty_words: int
    question_type: models.QuestionType
    words: list[str] | None


class GenerateMultipleChoice(pydantic.BaseModel):
    """
    Defines the needed data to generate multiple choice question
    """

    qty_options: int
    text_data: str | None
    user_input: str | None
    block_questions: list[str] | None


class GenerateQuestion(pydantic.BaseModel):
    """
    Defines the needed data to generate a simple question
    """

    question_type: models.QuestionType
    user_input: str | None
    text_data: str | None
    block_questions: list[str] | None
    question_theme: models.QuestionTheme | None


class GeneratedWords(pydantic.BaseModel):
    """
    Generated words
    """

    words: list[str]


class GeneratedText(pydantic.BaseModel):
    """
    Generated text
    """

    text: str


class GeneratedAnswer(pydantic.BaseModel):
    answer: str
    is_correct: bool


class GeneratedMultipleChoice(pydantic.BaseModel):
    """
    Generated multiple choice question
    """

    question: str
    answers: list[GeneratedAnswer]


class GeneratedQuestion(pydantic.BaseModel):
    """
    Generic generated question
    """

    question: str
