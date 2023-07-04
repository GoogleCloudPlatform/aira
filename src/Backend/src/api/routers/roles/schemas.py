"""
Module containing schemas for all roles endpoints
"""
import datetime
import uuid

import pydantic


class Role(pydantic.BaseModel):
    """
    Base schema related to the Role.
    """

    id: uuid.UUID
    display_name: dict[str, str]

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class RoleList(pydantic.BaseModel):
    """
    Schema related to the role request.
    """

    items: list[Role]
    pages: int
    current_page: int
    total: int


class RoleGet(Role):
    """
    Schema related to the Role.
    """

    description: dict[str, str]
    scopes: list[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime
