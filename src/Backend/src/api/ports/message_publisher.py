"""
Module related to the port of the secret manager.
"""
import abc

from api import typings


# pylint: disable=too-few-public-methods
class MessagePublisher(abc.ABC):
    """
    Port related to message publisher.
    """

    @abc.abstractmethod
    async def publish(self, message: typings.Message, topic: str | None = None) -> None:
        """
        Publish to a message queue.
        """
