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
Module for the organizations model, aka schools.
"""
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from api import db


class Organization(db.Base, db.DefaultColumns):
    """
    Organization model.
    """

    __tablename__ = "organizations"

    customer_id: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)

    name: Mapped[db.Str50]

    region: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    city: Mapped[db.Str50]
    state: Mapped[str] = mapped_column(sa.String(2))
