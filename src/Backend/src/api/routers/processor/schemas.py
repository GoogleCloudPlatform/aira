# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module that contains all schemas to the processor endpoint.
"""
import dataclasses
import uuid

import pydantic

from api import typings

# pylint: disable=too-few-public-methods


class PubsubMessage(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines required pubsub message.
    """

    data: bytes
    message_id: str = pydantic.Field(alias="messageId")


class PubsubRequest(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines required pubsub request.
    """

    message: PubsubMessage
    subscription: str


class PubsubData(pydantic.BaseModel, extra=pydantic.Extra.allow):
    """
    Defines only needed data that will be converted from pubsub.
    """

    result_id: uuid.UUID
    phrase_set_id: str
    audio: str
    words: list[str]


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
