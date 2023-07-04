"""
Module related to the port of result repository.
"""
import abc
import uuid

from api import models


class ResultRepository(abc.ABC):
    """
    Result repository implementation that returns exam data.
    """

    @abc.abstractmethod
    async def get(
        self,
        result_id: uuid.UUID,
    ) -> models.ExamUserQuestion:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        result_model: models.ExamUserQuestion,
    ) -> models.ExamUserQuestion:
        """
        Creates and return the result model.

        :param result_model: the result model parameter.
        """

    @abc.abstractmethod
    async def delete(self, result_model: models.ExamUserQuestion) -> None:
        """
        Method to delete a result.

        :param result_model: the result model parameter.
        """
