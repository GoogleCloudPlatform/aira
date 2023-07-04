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
