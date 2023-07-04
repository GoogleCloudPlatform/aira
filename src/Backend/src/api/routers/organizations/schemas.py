"""
Module containing schemas for all orgs endpoints
"""
import datetime
import uuid

import pydantic


class Organization(pydantic.BaseModel):
    """
    Base schema related to the Organization.
    """

    id: uuid.UUID
    customer_id: str | None
    name: str
    city: str
    region: str | None

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True


class OrganizationList(pydantic.BaseModel):
    """
    Schema related to the organization request.
    """

    items: list[Organization]
    pages: int
    current_page: int
    total: int


class OrganizationGet(Organization):
    """
    Schema related to the Organization.
    """

    state: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


class OrganizationCreate(pydantic.BaseModel):
    """
    Schema related to the creation of a Organization.
    """

    customer_id: str | None
    name: str
    city: str
    state: str
    region: str | None

    class Config:
        """
        Pydantic config to receive as an orm.
        """

        orm_mode = True
