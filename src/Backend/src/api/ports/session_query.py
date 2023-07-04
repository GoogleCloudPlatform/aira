"""
Module related to the port of the session repository.
"""
from __future__ import annotations

import abc
import uuid

from api import models


class SessionRepository(abc.ABC):
    """
    Session repository.
    """

    @abc.abstractmethod
    async def get(self, session_id: uuid.UUID) -> models.Session:
        """
        Method to get the session for the user.

        :param session_id: the id for the session.

        :returns: session model.

        :raises errors.NotFound: if there's no such session.
        """

    @abc.abstractmethod
    async def create(self, session_model: models.Session) -> models.Session:
        """
        Method to create a session for the user.

        :param session_model: the session model parameter.

        :returns: session model.
        """

    @abc.abstractmethod
    async def delete(self, session_model: models.Session) -> None:
        """
        Method to delete a session from a user.

        :param session_model: the session model parameter.
        """


class GetSession(abc.ABC):
    """
    Get Session individualized.
    """

    @abc.abstractmethod
    async def __call__(self, session_id: uuid.UUID) -> models.Session | None:
        """
        Method to get the session for the user.

        :param session_id: the id for the session.

        :returns: session model.
        """
