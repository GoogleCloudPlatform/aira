"""
Module related to the port of exam data.
"""

import abc
import typing
import uuid

from sqlalchemy.engine.row import Row

from api import models, typings


# pylint: disable=too-few-public-methods
class ExamRepository(abc.ABC):
    """
    Exam repository implementation that returns exam data.
    """

    @abc.abstractmethod
    async def get(self, exam_id: uuid.UUID) -> models.Exam:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        exam_model: models.Exam,
    ) -> models.Exam:
        """
        Creates and return the exam model.

        :param exam_model: the exam model parameter.
        """

    @abc.abstractmethod
    async def delete(self, exam_model: models.Exam) -> None:
        """
        Method to delete a exam.

        :param exam_model: the exam model parameter.
        """


class GetExam(abc.ABC):
    """
    Get exam by its name.
    """

    @abc.abstractmethod
    async def __call__(
        self, exam_id: uuid.UUID, groups: list[uuid.UUID] | None = None
    ) -> models.Exam:
        """
        Method to get a specific exam.

        :param exam_id: the exam identifier.
        """


class GetUsersExamDetails(abc.ABC):
    """
    Get exam by user and exam id.
    """

    @abc.abstractmethod
    async def __call__(
        self, exam_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Row[typing.Any]]:
        """
        Method to get a specific user exam.

        :param exam_id: the exam identifier.
        :param user_id: the user identifier.
        """


class ListExams(abc.ABC):
    """
    Query to get all exams.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        groups: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.Exam], typings.PaginationMetadata]:
        """
        Method to list all exams.
        """


class ListPendingExams(abc.ABC):
    """
    Query to get all exams pending for a user.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[
        list[tuple[models.Exam, models.ExamStatus | None]], typings.PaginationMetadata
    ]:
        """
        Method to list all exams.
        """


class ListExamsWithResults(abc.ABC):
    """
    Query to get all exams pending for a user.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> list[models.Exam]:
        """
        Method to list all exams with results.
        """


class ListPendingQuestions(abc.ABC):
    """
    Query to get all questions pending for a user.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
    ) -> list[models.Question]:
        """
        Method to list all pending questions.
        """


class GetPendingQuestion(abc.ABC):
    """
    Query to get a pending question.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> models.Question:
        """
        Method to get a pending question.
        """


class ListQuestionsWithStatus(abc.ABC):
    """
    Query to list all questions.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
    ) -> list[tuple[models.Question, models.ExamUserQuestion | None]]:
        """
        Method to list all questions.
        """


class QuestionRepository(abc.ABC):
    """
    Question repository implementation that returns exam data.
    """

    @abc.abstractmethod
    async def get(self, question_id: uuid.UUID) -> models.Question:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        question_model: models.Question,
    ) -> models.Question:
        """
        Creates and return the question model.

        :param question_model: the question model parameter.
        """

    @abc.abstractmethod
    async def delete(self, question_model: models.Question) -> None:
        """
        Method to delete a question.

        :param question_model: the question model parameter.
        """


class GetExamUserStatus(abc.ABC):
    """
    Query to get a pending question.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        user_id: uuid.UUID,
        exam_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> models.ExamUser | None:
        """
        Method to get a pending question.
        """
