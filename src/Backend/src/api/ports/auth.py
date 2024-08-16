"""
Module related to the port of any external auth.
"""

import abc
import typing


# pylint: disable=too-few-public-methods
class ExternalAuth(abc.ABC):
    """
    Port related to external auth.
    """

    @abc.abstractmethod
    async def login_from_token(self, token: str) -> dict[str, typing.Any]:
        """
        Login token based.
        """
