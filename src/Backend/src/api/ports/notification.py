"""
Module for interface of notification.
"""

import abc
import typing


class Notification(abc.ABC):
    """
    Base class for notifications
    """

    @abc.abstractmethod
    async def send(self, email: str, template_file: str, **kwargs: typing.Any) -> bool:
        """
        Sends the notification
        """
        raise NotImplementedError()
