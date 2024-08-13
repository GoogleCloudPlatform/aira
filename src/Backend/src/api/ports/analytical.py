"""
Module related to analytical stuff.
"""

import abc
import typing
from datetime import datetime

from api.helpers.schemas import AnalyticalResult as Result


class AnalyticalResult(abc.ABC):
    """
    Result data to analytical database.
    """

    @abc.abstractmethod
    async def save(self, result: Result) -> typing.Sequence[dict[str, typing.Any]]:
        """
        Save result data to analytical database.
        """

    @abc.abstractmethod
    async def get_student_results(
        self,
        school_region: str | None = None,
        school_city: str | None = None,
        exam_name: str | None = None,
        school_name: str | None = None,
        class_name: str | None = None,
        exam_start_date: datetime | None = None,
        exam_end_date: datetime | None = None,
        organizations: list[str] | None = None,
        groups: list[str] | None = None,
    ) -> typing.Sequence[dict[str, typing.Any]]:
        """
        Get student results from database.
        """
