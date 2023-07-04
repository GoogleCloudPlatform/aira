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
Module with the implementation of pubsub
"""
import dataclasses
import json

import google.pubsub_v1 as pubsub
from google.oauth2 import service_account

from api import ports, typings
from api.helpers import UUIDEncoder


# pylint: disable=too-few-public-methods
class MessagePublisher(ports.MessagePublisher):
    """
    Implementation of google's pubsub.
    """

    def __init__(self, project_id: str, creds_path: str, topic: str):
        credentials = None
        if creds_path:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path
            )
        self.client = pubsub.PublisherAsyncClient(credentials=credentials)
        self.project_id = project_id
        self.topic_path = self.client.topic_path(project_id, topic)

    async def publish(self, message: typings.Message, topic: str | None = None) -> None:
        topic_path = (
            self.topic_path
            if not topic
            else self.client.topic_path(self.project_id, topic)
        )
        pubsub_message = pubsub.PubsubMessage(
            data=json.dumps(
                dataclasses.asdict(message),  # type: ignore[call-overload]
                cls=UUIDEncoder,
            ).encode("utf-8")
        )
        await self.client.publish(messages=[pubsub_message], topic=topic_path)
