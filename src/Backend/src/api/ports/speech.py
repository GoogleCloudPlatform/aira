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
        model_type: str = "latest_short",
    ) -> str:
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
