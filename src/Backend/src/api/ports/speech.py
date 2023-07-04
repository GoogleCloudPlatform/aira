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
Module containing speech to text abstract.
"""
import abc
import typing


class SpeechToText(abc.ABC):
    """
    Speech to text abstract
    """

    # pylint: disable=too-many-arguments
    @abc.abstractmethod
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
    ) -> tuple[str, str, int]:
        """
        Method that processes the audio and returns list of data.
        """

    @abc.abstractmethod
    async def create_phrase_set(self, phrases: list[dict[str, typing.Any]]) -> str:
        """
        Method to build phrase set that will be used as context.
        """

    @abc.abstractmethod
    async def delete_phrase_set(self, phrase_set_id: str) -> None:
        """
        Method to delete a phrase set.
        """
