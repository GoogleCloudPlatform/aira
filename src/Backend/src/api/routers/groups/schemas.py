"""
Module containing schemas for all groups endpoints
"""

import datetime
import typing
import uuid

import pydantic

from api import errors
from api.routers.organizations import schemas


class Group(pydantic.BaseModel):
    """
    Base schema related to the Group.
    """

    id: uuid.UUID
    name: str
    grade: str = ""
    shift: str = ""
    series_id: uuid.UUID
    shift_id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @pydantic.root_validator(pre=True)
    @classmethod
    def extract_relations(cls, values: typing.Any) -> typing.Any:
        """
        Extract grade and shift string names from series and work_shift relations.
        """
        if not isinstance(values, dict):
            # ORM instance mapping (wrapped in a Pydantic GetterDict)
            series_obj = values.get("series")
            work_shift_obj = values.get("work_shift")

            grade_val = series_obj.name if series_obj else ""
            shift_val = work_shift_obj.code.lower() if work_shift_obj else ""

            res = {
                "id": values.get("id"),
                "name": values.get("name"),
                "grade": grade_val,
                "shift": shift_val,
                "series_id": values.get("series_id"),
                "shift_id": values.get("shift_id"),
                "created_at": values.get("created_at"),
                "updated_at": values.get("updated_at"),
            }

            # Dynamically copy subclass fields if present in GetterDict
            if values.get("organization") is not None:
                res["organization"] = values.get("organization")
            if values.get("customer_id") is not None:
                res["customer_id"] = values.get("customer_id")

            return res
        return values

    class Config:
        """
        Pydantic's config.
        """

        orm_mode = True


class GroupGet(Group):
    """
    Schema related to the Group.
    """

    customer_id: str | None
    organization: schemas.Organization


class OrgList(pydantic.BaseModel):
    """
    Schema related to the organization request.
    """

    id: uuid.UUID
    name: str

    class Config:
        """
        Pydantic's config.
        """

        orm_mode = True


class GroupList(Group):
    """
    Schema related to the Group.
    """

    organization: OrgList


class GroupCreate(pydantic.BaseModel):
    """
    Schema related to the creation of a new Group.
    """

    customer_id: str | None = None
    name: str
    series_id: uuid.UUID
    shift_id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class GroupsList(pydantic.BaseModel):
    """
    Schema related to the groups request.
    """

    items: list[GroupList]
    pages: int
    current_page: int
    total: int


class GroupPatch(pydantic.BaseModel):
    """
    Schema related to the update of a Group.
    """

    name: str | None = None
    customer_id: str | None = None
    series_id: uuid.UUID | None = None
    shift_id: uuid.UUID | None = None
    organization_id: uuid.UUID | None = None

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
