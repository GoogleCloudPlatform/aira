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
