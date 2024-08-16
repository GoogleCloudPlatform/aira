"""
Module containing schemas for all users endpoints
"""

import datetime
import uuid

import pydantic

from api import models
from api.routers.exams import schemas as exam_schemas
from api.routers.groups import schemas as group_schemas
from api.routers.organizations import schemas as org_schemas


class User(pydantic.BaseModel):
    """
    Base schema related to the User.
    """

    id: uuid.UUID
    name: str
    email_address: pydantic.EmailStr
    groups: list[group_schemas.Group]
    organizations: list[org_schemas.Organization]
    role_id: uuid.UUID

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class ExamWithStatus(exam_schemas.Exam):
    """
    Exam schema with status.
    """

    status: str | models.ExamStatus | None

    @pydantic.validator("status", pre=True, always=True)
    @classmethod
    def validate_status(cls, val: models.ExamStatus | str | None) -> str:
        """
        Validate the status of the exam.
        """
        if not val:
            return models.ExamStatus.NOT_STARTED.name
        if isinstance(val, models.ExamStatus):
            return val.name
        return val.upper()


class ExamWithStatusList(pydantic.BaseModel):
    """
    Schema related to the exam request.
    """

    items: list[ExamWithStatus]
    pages: int
    current_page: int
    total: int


class UserWithExams(pydantic.BaseModel):
    """
    Base schema related to the User.
    """

    id: uuid.UUID
    name: str
    email_address: pydantic.EmailStr
    role_id: uuid.UUID
    exams: list[ExamWithStatus] | None = []

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class UserList(pydantic.BaseModel):
    """
    Schema related to the user request.
    """

    items: list[User]
    pages: int
    current_page: int
    total: int


class UserWithExamsList(pydantic.BaseModel):
    """
    Schema related to the user request.
    """

    items: list[UserWithExams]
    pages: int
    current_page: int
    total: int


class UserGet(User):
    """
    Schema related to the User.
    """

    state: str | None
    county: str | None
    region: str | None
    external_id: str | None
    last_login: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class UserCreate(pydantic.BaseModel):
    """
    Schema related to the creation of a User.
    """

    role_id: uuid.UUID
    groups: list[uuid.UUID] = pydantic.Field(default_factory=list)
    organizations: list[uuid.UUID] = pydantic.Field(default_factory=list)
    name: str
    email_address: pydantic.EmailStr
    customer_id: str | None = None
    type: models.UserType
    password: pydantic.StrictStr | None = None
    external_id: str | None = None
    state: str | None = None
    county: str | None = None
    region: str | None = None

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class UserPatch(pydantic.BaseModel, orm_mode=True):
    """
    Schema related to the User patch.
    """

    name: str | None
    groups: list[uuid.UUID] | None
    organizations: list[uuid.UUID] | None
    state: str | None
    county: str | None
    region: str | None
