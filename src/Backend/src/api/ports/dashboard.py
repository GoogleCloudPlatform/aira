"""
Module related to all dashboard stuff.
"""

import abc
import typing

from starlette import datastructures

from api import models


class Dashboard(abc.ABC):
    """
    The port for the dashboard functions.
    """

    @abc.abstractmethod
    async def get_signed_url(
        self,
        user: models.User,
        query: datastructures.QueryParams,
    ) -> str:
        """
        Generates signed url to access the dashboard.
        """

    @abc.abstractmethod
    async def delete_looker_user(self, user_id: str) -> str:
        """
        Delete Looker User by user id
        """

    @abc.abstractmethod
    async def get_all_looker_users(self) -> typing.Any:
        """
        Get a list of all Looker Users.
        """
