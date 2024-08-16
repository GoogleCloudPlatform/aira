"""
Module containing custom typings
"""

from __future__ import annotations

import typing
import uuid

from pydantic import dataclasses
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import models

Settings = typing.NewType("Settings", dict[str, str])

SessionFactory: typing.TypeAlias = sqlalchemy_aio.async_sessionmaker[
    sqlalchemy_aio.AsyncSession
]


@dataclasses.dataclass(frozen=True)
class Paginated:
    """
    Dataclass for the pagination result from fastapi-pagination.
    """

    items: list[typing.Any]
    total: int
    page: int
    size: int
    pages: int


@dataclasses.dataclass(frozen=True)
class PaginationMetadata:
    """
    Dataclass for the pagination metadata.
    """

    current_page: int
    total_pages: int
    total_items: int
    page_size: int


class Message:
    """
    Publisher abstract messages.
    """


@dataclasses.dataclass
class CreateOrUpdateOrganization:
    """
    Create or update Organization model.
    """

    customer_id: str | None
    name: str
    region: str | None
    city: str
    state: str
    county: str


@dataclasses.dataclass
class CreateOrUpdateGroup:
    name: str
    customer_id: str | None
    grade: models.Grades
    shift: models.Shifts


@dataclasses.dataclass
class CreateOrUpdateUser:
    """
    User for create or update model.
    """

    external_id: str | None
    customer_id: str | None
    type: models.UserType
    role_id: uuid.UUID
    name: str
    email_address: str
    state: str | None
    region: str | None
    county: str | None
    orgs_customer_id: list[str] | None
    groups_customer_id: list[str] | None
