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
    MULTIPLE_CHOICE = "multiple_choice"
    UNDERSTANDING_CHECK = "understanding_check"
    LOGICAL_SITUATIONS = "logical_situations"
    SHORT_EXPLANATIONS = "short_explanations"
    INDUSTRY_AREAS = "industry_areas"

    @classmethod
    def _missing_(cls, value: object) -> enum.StrEnum | None:
        value = str(value).lower()
        for member in cls:
            if member.lower() == value:
                return member
        return None


class QuestionTheme(enum.StrEnum):
    """
    Question Theme.
    """

    MONICA_AGUA_BOA = "monica_agua_boa"
    O_MENINO_MALUQUINHO = "o_menino_maluquinho"
    O_PEQUENO_PRINCIPE = "o_pequeno_principe"

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
    theme: Mapped[QuestionTheme | None] = mapped_column(
        psql.ENUM(QuestionTheme), nullable=True
    )
    phrase_id: Mapped[db.Str100]
    data: Mapped[str] = mapped_column(sa.Text, nullable=False)
    formatted_data: Mapped[str] = mapped_column(sa.Text, nullable=False)
    order: Mapped[int] = mapped_column(sa.SmallInteger, nullable=False)
    answers: Mapped[db.ListDictJSON | None]


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

    ai_exam_feedback: Mapped[str | None] = mapped_column(
        sa.String(1000), nullable=True, default=None
    )

    __table_args__ = (sa.Index("ix_exam_user_exam_user_id", "exam_id", "user_id"),)


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

    __table_args__ = (
        sa.Index("ix_exam_start_end_date", "start_date", "end_date"),
        sa.Index("ix_exam_grade", "grade"),
    )


class ExamUserQuestion(db.Base, db.DefaultColumns):
    """
    Table to relate user/exam to get results.
    """

    __tablename__ = "exams_users_questions"

    __table_args__ = (
        sa.UniqueConstraint("user_id", "exam_id", "question_id", name="ueq_uc"),
        sa.Index("ix_exam_user_question_user_exam_id", "user_id", "exam_id"),
        sa.Index("ix_exam_user_question_question_id", "question_id"),
        sa.Index(
            "ix_exam_user_question_group_organization_id", "group_id", "organization_id"
        ),
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

    ai_feedback: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    ai_is_correct: Mapped[bool | None] = mapped_column(sa.Boolean, nullable=True)

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
