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
Base models startup
"""
from __future__ import annotations

import datetime
import typing
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from api.helpers import time_now

Str50 = typing.Annotated[str, mapped_column(sa.String(50))]
Str100 = typing.Annotated[str, mapped_column(sa.String(100))]
DictJSON = typing.Annotated[dict[str, str], mapped_column(psql.JSON, nullable=False)]
ListJSON = typing.Annotated[
    list[str], mapped_column(psql.JSONB(none_as_null=True), nullable=False)
]
UuidPk = typing.Annotated[
    uuid.UUID,
    mapped_column(psql.UUID(as_uuid=True), primary_key=True),
]
UuidDefault = typing.Annotated[
    uuid.UUID,
    mapped_column(psql.UUID(as_uuid=True)),
]
DateTime = typing.Annotated[
    datetime.datetime,
    mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    ),
]


class Base(MappedAsDataclass, DeclarativeBase):
    """
    Creating a base from Base.
    """

    __mapper_args__ = {"eager_defaults": True}
    __allow_unmapped__ = True


class DefaultColumns:
    """
    Adding default columns
    """

    id: Mapped[UuidPk] = mapped_column(
        init=False, default_factory=uuid.uuid4, sort_order=-1
    )

    created_at: Mapped[DateTime] = mapped_column(
        init=False, default_factory=time_now, sort_order=1
    )

    updated_at: Mapped[DateTime] = mapped_column(
        init=False,
        default_factory=time_now,
        onupdate=time_now,
        sort_order=2,
    )
