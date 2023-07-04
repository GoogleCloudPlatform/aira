"""
Module related to all dashboard stuff.
"""
import abc

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
