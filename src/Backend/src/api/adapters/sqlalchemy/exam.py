"""
Module for all exam related sqlalchemy queries.
"""

import logging
import typing
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc
from sqlalchemy.engine.row import Row
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

        :param exam_id: exam id on database.
        :param name: name on database.

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


class GetUsersExamDetails(ports.GetUsersExamDetails):
    """
    Get exam details by its id and user id.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self, exam_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Row[typing.Any]]:
        """
        Method to get a specific user exam.

        :param exam_id: the exam identifier.
        :param user_id: the user identifier.
        """
        exam = models.Exam
        euq = models.ExamUserQuestion
        eu = models.ExamUser
        question = models.Question
        exam_stmt = (
            sa.select(
                exam,
                sa.cast(
                    sa.func.json_agg(
                        sa.func.json_build_object(
                            "id",
                            question.id,
                            "name",
                            question.name,
                            "data",
                            question.data,
                            "formatted_data",
                            question.formatted_data,
                            "type",
                            question.type,
                            "order",
                            question.order,
                            "response",
                            sa.func.json_build_object(
                                "result",
                                euq.result,
                                "right_count",
                                euq.right_count,
                                "status",
                                euq.status,
                                "created_at",
                                euq.created_at,
                                "updated_at",
                                euq.updated_at,
                                "audio_url",
                                euq.audio_url,
                                "user_rating",
                                eu.user_rating,
                                "user_accuracy",
                                euq.user_accuracy,
                                "total_accuracy",
                                euq.total_accuracy,
                            ),
                        )
                    ),
                    type_=sa.String,
                ).label("questions"),
            )
            .join(euq, sa.and_(euq.user_id == user_id, exam.id == euq.exam_id))
            .join(eu, sa.and_(eu.exam_id == exam.id, eu.user_id == user_id))
            .join(
                question,
                sa.and_(question.id == euq.question_id, question.exam_id == exam.id),
            )
            .where(exam.id == exam_id)
            .group_by(exam.id)
        )

        async with self._session_factory() as session:
            result = await session.execute(exam_stmt)
        exam_result = list(result.unique().all())

        return exam_result


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
            stmt = stmt.join(
                models.Group,
                sa.and_(
                    models.Group.id.in_(groups),
                    models.Group.grade == models.Exam.grade,
                ),
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
    ) -> tuple[
        list[tuple[models.Exam, models.ExamStatus | None]], typings.PaginationMetadata
    ]:
        exam_user = models.ExamUser
        current_date = helpers.time_now()
        group = models.Group
        exam = models.Exam
        stmt = (
            sa.select(exam, exam_user.status)
            .join(
                group,
                sa.and_(
                    group.grade == exam.grade,
                    group.id == group_id,
                ),
            )
            .outerjoin(
                exam_user,
                sa.and_(exam_user.exam_id == exam.id, exam_user.user_id == user_id),
            )
            .where(
                exam.start_date <= current_date,
            )
            .where(exam.end_date > current_date)
            .where(
                sa.or_(
                    exam_user.status != models.ExamStatus.FINISHED,
                    exam_user.exam_id.is_(None),
                )
            )
        )

        async with self._session_factory() as session:
            if page_size >= 0:
                params = Params(page=page, size=page_size)
                result: typings.Paginated = await paginate(session, stmt, params=params)
                result_items = result.items
                current_page = result.page
                total_pages = result.pages
                total_items = result.total
                page_size = result.size
            else:
                result_all = await session.execute(stmt)
                result_items = list(result_all.scalars().unique())
                current_page = 1
                total_pages = 1
                total_items = len(result_items)
                page_size = len(result_items)

        return result_items, typings.PaginationMetadata(
            current_page=current_page,
            total_pages=total_pages,
            total_items=total_items,
            page_size=page_size,
        )


class ListExamsWithResults(ports.ListExamsWithResults):
    """
    Query to get all exams.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        user_id: uuid.UUID,
        group_id: uuid.UUID,
    ) -> list[models.Exam]:
        exam_user = models.ExamUser
        current_date = helpers.time_now()
        group = models.Group
        exam = models.Exam
        stmt = (
            sa.select(exam)
            .join(
                group,
                sa.and_(
                    group.grade == exam.grade,
                    group.id == group_id,
                ),
            )
            .join(
                exam_user,
                sa.and_(
                    exam_user.exam_id == exam.id,
                    exam_user.user_id == user_id,
                    exam_user.status == models.ExamStatus.FINISHED,
                ),
            )
            .where(
                exam.start_date <= current_date,
            )
        )

        async with self._session_factory() as session:
            result_all = await session.execute(stmt)

        return list(result_all.scalars().unique())


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
                sa.or_(Euq.user_id.is_(None), Euq.status != models.ExamStatus.FINISHED)
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
            .order_by(Question.order.asc())
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

        :param question_id: question id on database.
        :param name: name on database.

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
