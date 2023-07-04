"""
Module with the Memory implementation for external auths.
"""
import logging
import typing

from api import ports

logger = logging.getLogger(__name__)


class ExternalAuth(ports.ExternalAuth):
    """
    Memory implementation for external auth.
    """

    async def login_from_token(self, token: str) -> dict[str, typing.Any]:
        """
        Login token based.
        """
        return {"uid": "test-user"}
