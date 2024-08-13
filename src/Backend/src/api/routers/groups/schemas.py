"""
Module containing schemas for all groups endpoints
"""

import datetime
import typing
import uuid

import pydantic

from api import errors, models
from api.routers.organizations import schemas


class Group(pydantic.BaseModel):
    """
    Base schema related to the Group.
    """

    id: uuid.UUID
    customer_id: str | None
    name: str

    class Config:
        """
        Pydantic's config.
        """

        orm_mode = True


class GroupGet(Group):
    """
    Schema related to the Group.
    """

    grade: models.Grades
    shift: str
    organization: schemas.Organization
    created_at: datetime.datetime
    updated_at: datetime.datetime


class GroupCreate(pydantic.BaseModel):
    """
    Schema related to the creation of a new Group.
    """

    customer_id: str | None
    name: str
    grade: models.Grades
    shift: models.Shifts
    organization_id: uuid.UUID

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True
        use_enum_values = False


class GroupsList(pydantic.BaseModel):
    """
    Schema related to the groups request.
    """

    items: list[GroupGet]
    pages: int
    current_page: int
    total: int


class GroupPatch(pydantic.BaseModel):
    """
    Schema related to the update of a Group.
    """

    name: str | None
    customer_id: str | None
    grade: models.Grades | None
    shift: str | None
    organization_id: uuid.UUID | None

    @pydantic.root_validator(pre=True)
    @classmethod
    def prevent_none(cls, values: dict[str, typing.Any]) -> dict[str, typing.Any]:
        """
        Validator to ensure that, if the field is sent, it's not None.
        """
        for k, val in values.items():
            if val is None:
                raise errors.FieldNotNullable(field=k)
        return values
