"""
Module for all exam related sqlalchemy queries.
"""
import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, helpers, models, ports, typings

logger = logging.getLogger(__name__)


class ExamRepository(ports.ExamRepository):
    """
    Exam repository implementation that returns exam data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, exam_id: uuid.UUID) -> models.Exam:
        """
        Get exam by params.

        :params exam_id: exam id on database.
        :params name: name on database.

        :raises errors.NotFound: if the entity was not found.
        """
        stmt = sa.select(models.Exam)
        if exam_id:
            stmt = stmt.where(models.Exam.id == exam_id)

        result = await self._session.execute(stmt)
        if not (exam := result.unique().scalars().one_or_none()):
            raise errors.NotFound("exam")
        return exam

    async def create(self, exam_model: models.Exam) -> models.Exam:
        """
        Method to create a exam.

        :param exam_model: the exam model parameter.

        :returns: exam model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(exam_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        return exam_model

    async def delete(self, exam_model: models.Exam) -> None:
        """
        Method to delete a exam.

        :param exam_model: the exam model parameter.
        """
        await self._session.delete(exam_model)


class GetExam(ports.GetExam):
    """
    Get exam by its name.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self, exam_id: uuid.UUID, groups: list[uuid.UUID] | None = None
    ) -> models.Exam:
        """
        Method to get a specific exam.

        :param exam_id: the exam identifier.
        """
        stmt = sa.select(models.Exam).where(models.Exam.id == exam_id)
        if groups is not None:
            stmt = stmt.join(
                models.Group,
                sa.and_(
                    models.Group.id.in_(groups), models.Group.grade == models.Exam.grade
                ),
            )
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (exam := result.scalars().unique().one_or_none()):
            raise errors.NotFound("exam")

        return exam


class ListExams(ports.ListExams):
    """
    Query to get all exams.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

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
        stmt = sa.select(models.Exam).order_by(models.Exam.start_date.desc())

        if groups is not None:
            stmt = stmt.join(models.Group).where(
                sa.and_(
                    models.Group.id.in_(groups),
                    models.Group.grade == models.Exam.grade,
                )
            )
        if query:
            stmt = stmt.where(
                sa.or_(
                    models.Exam.name.ilike(f"%{query}%"),
                )
            )
        params = Params(page=page, size=page_size)
        async with self._session_factory() as session:
            result: typings.Paginated = await paginate(
                session, stmt, params=params, unique=True
            )
        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class ListPendingExams(ports.ListPendingExams):
    """
    Query to get all exams.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[models.Exam], typings.PaginationMetadata]:
        exam_user = models.ExamUser
        current_date = helpers.time_now()
        stmt = (
            sa.select(models.Exam)
            .join(
                models.Group,
                sa.and_(
                    models.Group.grade == models.Exam.grade,
                    models.Group.id == group_id,
                ),
            )
            .outerjoin(
                exam_user,
                sa.and_(
                    exam_user.exam_id == models.Exam.id, exam_user.user_id == user_id
                ),
            )
            .where(
                sa.or_(
                    exam_user.status != models.ExamStatus.FINISHED,
                    exam_user.exam_id.is_(None),
                )
            )
            .where(
                models.Exam.start_date <= current_date,
            )
            .where(models.Exam.end_date > current_date)
        )
        params = Params(page=page, size=page_size)

        async with self._session_factory() as session:
            result: typings.Paginated = await paginate(session, stmt, params=params)

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class ListPendingQuestions(ports.ListPendingQuestions):
    """
    Query to get all questions pending.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
    ) -> list[models.Question]:
        Question = models.Question
        Euq = models.ExamUserQuestion
        current_date = helpers.time_now()
        stmt = (
            sa.select(Question)
            .join(models.Exam, models.Exam.id == Question.exam_id)
            .join(models.Group, models.Group.grade == models.Exam.grade)
            .outerjoin(
                Euq,
                sa.and_(
                    Euq.question_id == Question.id,
                    Euq.user_id == user_id,
                    Euq.exam_id == exam_id,
                ),
            )
            .where(
                sa.or_(
                    Euq.user_id.is_(None), Euq.status == models.ExamStatus.NOT_STARTED
                )
            )
            .where(Question.exam_id == exam_id)
            .where(models.Group.id == group_id)
            .where(
                models.Exam.start_date <= current_date,
            )
            .where(models.Exam.end_date > current_date)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
        questions = list(result.scalars().unique())
        return questions


class GetPendingQuestion(ports.GetPendingQuestion):
    """
    Query to get a pending question.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
        question_id: uuid.UUID,
    ) -> models.Question:
        Question = models.Question
        ExamUQ = models.ExamUserQuestion
        current_date = helpers.time_now()
        stmt = (
            sa.select(Question)
            .join(models.Exam, models.Exam.id == Question.exam_id)
            .outerjoin(
                ExamUQ,
                sa.and_(
                    ExamUQ.question_id == Question.id,
                    ExamUQ.user_id == user_id,
                    ExamUQ.group_id == group_id,
                    ExamUQ.exam_id == exam_id,
                ),
            )
            .where(Question.id == question_id)
            .where(ExamUQ.question_id.is_(None))
            .where(
                models.Exam.start_date <= current_date,
            )
            .where(models.Exam.end_date > current_date)
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (question := result.scalars().unique().one_or_none()):
            raise errors.NotPending

        return question


class ListQuestionsWithStatus(ports.ListQuestionsWithStatus):
    """
    Query to get all questions pending.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
        exam_id: uuid.UUID,
    ) -> list[tuple[models.Question, models.ExamUserQuestion | None]]:
        Question = models.Question
        Euq = models.ExamUserQuestion
        current_date = helpers.time_now()
        stmt = (
            sa.select(Question, models.ExamUserQuestion)
            .join(models.Exam, models.Exam.id == Question.exam_id)
            .join(models.Group, models.Group.grade == models.Exam.grade)
            .outerjoin(
                Euq,
                sa.and_(
                    Euq.question_id == Question.id,
                    Euq.user_id == user_id,
                    Euq.exam_id == exam_id,
                ),
            )
            .where(Question.exam_id == exam_id)
            .where(models.Group.id == group_id)
            .where(
                models.Exam.start_date <= current_date,
            )
            .where(models.Exam.end_date > current_date)
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
        response = [(res[0], res[1]) for res in result.unique()]
        return response


class QuestionRepository(ports.QuestionRepository):
    """
    Question repository implementation that returns question data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, question_id: uuid.UUID) -> models.Question:
        """
        Get question by params.

        :params question_id: question id on database.
        :params name: name on database.

        :raises errors.NotFound: if the entity was not found.
        """
        stmt = sa.select(models.Question)
        if question_id:
            stmt = stmt.where(models.Question.id == question_id)

        result = await self._session.execute(stmt)
        if not (question := result.scalars().one_or_none()):
            raise errors.NotFound("question")
        return question

    async def create(self, question_model: models.Question) -> models.Question:
        """
        Method to create a question.

        :param question_model: the question model parameter.

        :returns: question model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(question_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        return question_model

    async def delete(self, question_model: models.Question) -> None:
        """
        Method to delete a question.

        :param question_model: the question model parameter.
        """
        await self._session.delete(question_model)


class GetExamUserStatus(ports.GetExamUserStatus):
    """
    Get table exam_user.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        user_id: uuid.UUID,
        exam_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> models.ExamUser | None:
        """
        Method to get a specific exam.

        :param exam_id: the exam identifier.
        """
        stmt = (
            sa.select(models.ExamUser)
            .join(models.Exam, models.Exam.id == models.ExamUser.exam_id)
            .join(
                models.Group,
                sa.and_(
                    models.Group.grade == models.Exam.grade, models.Group.id == group_id
                ),
            )
            .where(models.ExamUser.exam_id == exam_id)
            .where(models.ExamUser.user_id == user_id)
            .where()
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (exam_user := result.scalars().unique().one_or_none()):
            return None

        return exam_user
