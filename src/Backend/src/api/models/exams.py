# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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


class QuestionType(enum.StrEnum):
    """
    Exam status.
    """

    WORDS = "words"
    PHRASES = "phrases"


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
