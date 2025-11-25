"""
Module that contains all schemas to the processor endpoint.
"""

import dataclasses
import uuid

import pydantic

from api import models, typings
from api.helpers import schemas

# pylint: disable=too-few-public-methods


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


class PubsubEmailData(pydantic.BaseModel):
    """
    Defines only needed data that will be used to send email.
    """

    grade: models.Grades


class CreateSignedRequest(pydantic.BaseModel):
    """
    Defines the base data to create a signed url
    """

    file_type: str
    mimetype: str


class CreateUserSignedRequest(CreateSignedRequest):
    """
    Defines the needed data to create a signed url for users
    """

    exam_id: uuid.UUID
    question_id: uuid.UUID
    user_id: uuid.UUID


class CreateImportSignedRequest(CreateSignedRequest):
    """
    Defines the needed data to create a signed url for users
    """

    type: schemas.ImportType


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
