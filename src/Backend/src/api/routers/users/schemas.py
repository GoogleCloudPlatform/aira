"""
Module containing schemas for all users endpoints
"""
import datetime
import uuid

import pydantic

from api import models
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


class UserList(pydantic.BaseModel):
    """
    Schema related to the user request.
    """

    items: list[User]
    pages: int
    current_page: int
    total: int


class UserGet(pydantic.BaseModel):
    """
    Schema related to the User.
    """

    id: uuid.UUID
    name: str
    groups: list[group_schemas.Group]
    organizations: list[org_schemas.Organization]
    role_id: uuid.UUID
    external_id: str | None
    email_address: pydantic.EmailStr
    last_login: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class UserCreate(pydantic.BaseModel):
    """
    Schema related to the creation of a User.
    """

    role_id: uuid.UUID
    groups: list[uuid.UUID] = pydantic.Field(default_factory=list)
    organizations: list[uuid.UUID] = pydantic.Field(default_factory=list)
    name: str
    email_address: pydantic.EmailStr
    customer_id: uuid.UUID | None = None
    type: models.UserType
    password: pydantic.StrictStr | None = None
    external_id: str | None = None

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
