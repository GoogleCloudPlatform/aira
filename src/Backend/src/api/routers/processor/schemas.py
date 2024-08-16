"""
Module that contains all schemas to the processor endpoint.
"""

import dataclasses
import uuid

import pydantic

from api import typings
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


class PubsubDataReprocessed(PubsubData):
    """
    Defines only needed data that will be converted from pubsub.
    """

    duration: int
    sample_rate: int | None
    channels: int | None


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
