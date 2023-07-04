"""
Module related to analytical stuff.
"""
import abc

from api.helpers.schemas import AnalyticalResult as Result


class AnalyticalResult(abc.ABC):
    """
    Result data to analytical database.
    """

    @abc.abstractmethod
    async def save(self, result: Result) -> bool:
        """
        Save result data to analytical database.
        """
