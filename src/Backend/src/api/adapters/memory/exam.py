"""
Module for all exam related sqlalchemy memory implementation queries.
"""

import uuid

from api import errors, models, ports, typings
from api.helpers import time_now


class ExamRepository(ports.ExamRepository):
    """
    Exam repository memory implementation that returns exam data.
    """

    def __init__(self, items: list[models.Exam] | None = None) -> None:
        self._items = items if items else []

    async def get(self, exam_id: uuid.UUID) -> models.Exam:
        """
        Get exam by params.

        :param exam_id: exam id on database.
        :param name: name on database.
        """
        if self._items:
            items = self._items
            if exam_id:
                items = [item for item in items if item.id == exam_id]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(self, exam_model: models.Exam) -> models.Exam:
        """
        Method to create a exam for the exam.

        :param exam_model: the exam model parameter.

        :returns: exam model.
        """
        if any(item for item in self._items if item.id == exam_model.id):
            raise errors.AlreadyExists()
        exam_model.created_at = exam_model.updated_at = time_now()
        self._items.append(exam_model)
        return exam_model

    async def delete(self, exam_model: models.Exam) -> None:
        """
        Method to delete a exam.

        :param exam_model: the exam model parameter.
        """
        self._items = [item for item in self._items if item.id != exam_model.id]


class ListExams(ports.ListExams):
    """
    Query to get all exams.
    """

    def __init__(self, exams: list[models.Exam] | None = None) -> None:
        self._items = exams if exams else []
        self.called = 0

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
        items = self._items
        if query:
            items = [
                item for item in items if query in item.name or query in item.grade
            ]
        self.called += 1

        return items[
            (page - 1) * page_size : page * page_size
        ], typings.PaginationMetadata(
            current_page=page,
            total_pages=len(items) // page_size,
            page_size=page_size,
            total_items=len(self._items),
        )


class GetExam(ports.GetExam):
    """
    Query to get a specific exam.
    """

    def __init__(self, exams: list[models.Exam] | None = None) -> None:
        self._items = exams if exams else []

    async def __call__(
        self, exam_id: uuid.UUID, groups: list[uuid.UUID] | None = None
    ) -> models.Exam:
        """
        Method to get a specific exam.

        :param exam_id: the exam identifier.
        """
        items = self._items
        exams = [item for item in items if item.id == exam_id]
        if len(exams) != 1:
            raise errors.NotFound()
        return exams[0]


class QuestionRepository(ports.QuestionRepository):
    """
    Question repository memory implementation that returns question data.
    """

    def __init__(self, items: list[models.Question] | None = None) -> None:
        self._items = items if items else []

    async def get(self, question_id: uuid.UUID) -> models.Question:
        """
        Get question by params.

        :param question_id: question id on database.
        :param name: name on database.
        """
        if self._items:
            items = self._items
            if question_id:
                items = [item for item in items if item.id == question_id]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(self, question_model: models.Question) -> models.Question:
        """
        Method to create a question for the question.

        :param question_model: the question model parameter.

        :returns: question model.
        """
        if any(item for item in self._items if item.id == question_model.id):
            raise errors.AlreadyExists()
        question_model.created_at = question_model.updated_at = time_now()
        self._items.append(question_model)
        return question_model

    async def delete(self, question_model: models.Question) -> None:
        """
        Method to delete a question.

        :param question_model: the question model parameter.
        """
        self._items = [item for item in self._items if item.id != question_model.id]


class ListPendingQuestions(ports.ListPendingQuestions):
    """
    Query to get a specific exam.
    """

    def __init__(self, exams: list[models.Question] | None = None) -> None:
        self._items = exams if exams else []

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
    ) -> list[models.Question]:
        """
        Method to get a specific exam.

        :param exam_id: the exam identifier.
        """
        items = self._items
        items = [item for item in items if item.exam_id == exam_id]
        return items


class GetExamUserStatus(ports.GetExamUserStatus):
    """
    Query to get a specific exam user status.
    """

    def __init__(self, exams: list[models.ExamUser] | None = None) -> None:
        self._items = exams if exams else []

    async def __call__(
        self,
        user_id: uuid.UUID,
        exam_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> models.ExamUser:
        """
        Method to get a specific exam.

        :param user_id: the user identifier.
        :param exam_id: the exam identifier.
        """
        items = self._items
        items = [item for item in items if item.user_id == user_id]
        items = [item for item in items if item.exam_id == exam_id]
        if len(items) != 1:
            raise errors.NotFound()
        return items[0]


class ListPendingExams(ports.ListPendingExams):
    """
    Query to get a specific exam.
    """

    def __init__(
        self,
        exams_with_status: (
            list[tuple[models.Exam, models.ExamStatus | None]] | None
        ) = None,
    ) -> None:
        self._items = exams_with_status if exams_with_status else []

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
        items = self._items
        return items[
            (page - 1) * page_size : page * page_size
        ], typings.PaginationMetadata(
            current_page=page,
            total_pages=len(items) // page_size,
            page_size=page_size,
            total_items=len(self._items),
        )


class ListExamsWithResults(ports.ListExamsWithResults):
    """
    Query to get a specific exam.
    """

    def __init__(
        self,
        exams: list[models.Exam] | None = None,
    ) -> None:
        self._items = exams or []

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> list[models.Exam]:
        """
        Method to list all exams.
        """
        items = self._items
        return items
