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
