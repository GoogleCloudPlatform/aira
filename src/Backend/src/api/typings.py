"""
Module containing custom typings
"""
from __future__ import annotations

import typing

from pydantic import dataclasses
from sqlalchemy.ext import asyncio as sqlalchemy_aio

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
