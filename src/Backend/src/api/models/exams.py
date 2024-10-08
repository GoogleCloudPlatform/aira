"""
Module for the groups model, aka classes.
"""

import datetime
import enum

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api import db

from .groups import Grades, Group
from .organizations import Organization
from .users import User


class ExamStatus(enum.StrEnum):
    """
    Exam status.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class UserRating(enum.StrEnum):
    """
    User rating.
    """

    NO_RATING = "Sem Classificação"
    FLUENT = "Leitor Fluente"
    READER = "Leitor Iniciante"
    PRE_READER_ONE = "Pré-leitor 1"
    PRE_READER_TWO = "Pré-leitor 2"
    PRE_READER_THREE = "Pré-leitor 3"
    PRE_READER_FOUR = "Pré-leitor 4"

    @classmethod
    def _missing_(cls, value):  # type: ignore[no-untyped-def]
        # Em determinado momento, o READER trocou de Leitor para Leitor Iniciante
        # Este if conserta as entradas antigas salvas
        if value == "Leitor":
            return cls.READER
        return cls.NO_RATING


class QuestionType(enum.StrEnum):
    """
    Exam status.
    """

    WORDS = "words"
    COMPLEX_WORDS = "complex_words"
    PHRASES = "phrases"

    @classmethod
    def _missing_(cls, value: object) -> enum.StrEnum | None:
        value = str(value).lower()
        for member in cls:
            if member.lower() == value:
                return member
        return None


class Question(db.Base, db.DefaultColumns):
    """
    Question model.
    """

    __tablename__ = "questions"

    exam_id: Mapped[db.UuidDefault] = mapped_column(
        sa.ForeignKey("exams.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        init=False,
    )
    name: Mapped[db.Str50]
    type: Mapped[QuestionType] = mapped_column(psql.ENUM(QuestionType))
    phrase_id: Mapped[db.Str100]
    data: Mapped[str] = mapped_column(sa.Text, nullable=False)
    formatted_data: Mapped[str] = mapped_column(sa.Text, nullable=False)
    order: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)


class ExamUser(db.Base):
    """
    Exam/User model.
    """

    __tablename__ = "exams_users"

    exam_id: Mapped[db.UuidPk] = mapped_column(
        sa.ForeignKey("exams.id", ondelete="CASCADE")
    )
    user_id: Mapped[db.UuidPk] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    status: Mapped[ExamStatus] = mapped_column(
        psql.ENUM(ExamStatus), default=ExamStatus.NOT_STARTED
    )
    user_rating: Mapped[UserRating] = mapped_column(
        psql.ENUM(UserRating), default=UserRating.NO_RATING
    )
    created_at: Mapped[db.DateTime] = mapped_column(
        init=False, default=datetime.datetime.now(tz=datetime.UTC)
    )

    updated_at: Mapped[db.DateTime] = mapped_column(
        init=False,
        onupdate=datetime.datetime.now(tz=datetime.UTC),
        default=datetime.datetime.now(tz=datetime.UTC),
    )


class Exam(db.Base, db.DefaultColumns):
    """
    Exam model.
    """

    __tablename__ = "exams"

    name: Mapped[db.Str50]

    start_date: Mapped[db.DateTime]

    end_date: Mapped[db.DateTime]

    grade: Mapped[Grades] = mapped_column(psql.ENUM(Grades), nullable=False)

    questions: Mapped[list[Question]] = relationship(
        Question,
        lazy="joined",
        cascade="all, delete-orphan, save-update",
        order_by=Question.order.asc(),
    )


class ExamUserQuestion(db.Base, db.DefaultColumns):
    """
    Table to relate user/exam to get results.
    """

    __tablename__ = "exams_users_questions"

    __table_args__ = (
        sa.UniqueConstraint("user_id", "exam_id", "question_id", name="ueq_uc"),
    )

    user_id: Mapped[db.UuidDefault]
    exam_id: Mapped[db.UuidDefault]
    question_id: Mapped[db.UuidDefault]

    group_id: Mapped[db.UuidDefault]
    organization_id: Mapped[db.UuidDefault]

    result: Mapped[db.ListJSON]

    right_count: Mapped[int] = mapped_column(sa.Integer)

    user_accuracy: Mapped[float] = mapped_column(sa.FLOAT, nullable=False)
    total_accuracy: Mapped[float] = mapped_column(sa.FLOAT, nullable=False)

    audio_url: Mapped[str] = mapped_column(sa.String(400))

    status: Mapped[ExamStatus] = mapped_column(
        psql.ENUM(ExamStatus), default=ExamStatus.IN_PROGRESS, init=False
    )

    organization: Mapped[Organization] = relationship(
        Organization,
        primaryjoin="foreign(ExamUserQuestion.organization_id) == Organization.id",
        init=False,
        lazy="joined",
    )

    user: Mapped[User] = relationship(
        User,
        primaryjoin="foreign(ExamUserQuestion.user_id) == User.id",
        init=False,
        lazy="joined",
    )

    group: Mapped[Group] = relationship(
        Group,
        primaryjoin="foreign(ExamUserQuestion.group_id) == Group.id",
        init=False,
        lazy="joined",
    )

    exam: Mapped[Exam] = relationship(
        Exam,
        primaryjoin="foreign(ExamUserQuestion.exam_id) == Exam.id",
        init=False,
        lazy="joined",
    )
