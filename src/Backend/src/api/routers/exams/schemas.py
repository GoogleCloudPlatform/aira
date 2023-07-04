"""
Module containing schemas for all exams endpoints
"""
import dataclasses
import datetime
import typing
import uuid

import pydantic

from api import errors, models, typings


class Question(pydantic.BaseModel):
    """
    Base schema for questions.
    """

    name: str
    data: str
    type: models.QuestionType

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class QuestionListStatusless(Question):
    """
    Base schema for questions list.
    """

    id: uuid.UUID


class QuestionList(QuestionListStatusless):
    """
    Base schema for questions list.
    """

    status: models.ExamStatus | None


class Exam(pydantic.BaseModel):
    """
    Base schema related to the Exam.
    """

    id: uuid.UUID
    name: str
    start_date: datetime.datetime
    end_date: datetime.datetime

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class ExamList(pydantic.BaseModel):
    """
    Schema related to the exam request.
    """

    items: list[Exam]
    pages: int
    current_page: int
    total: int


class ExamGet(Exam):
    """
    Schema related to the Exam.
    """

    questions: list[QuestionListStatusless]
    grade: models.Grades
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ExamCreate(pydantic.BaseModel):
    """
    Schema related to the creation of exams.
    """

    name: str
    questions: list[Question]
    grade: models.Grades
    start_date: datetime.datetime
    end_date: datetime.datetime

    @pydantic.root_validator(pre=True)
    @classmethod
    def validate_dates(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Validate if the start date is before the end date.
        """
        if values["start_date"] > values["end_date"]:
            raise errors.StartDateError()
        return values

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class QuestionPost(pydantic.BaseModel):
    """
    Schema related to the post of questions.
    """

    url: pydantic.AnyHttpUrl


@dataclasses.dataclass
class QuestionMessage(typings.Message):
    """
    Dataclass for message sent to pubsub
    """

    result_id: uuid.UUID
    words: list[str]
    phrase_set_id: str
    audio: str
