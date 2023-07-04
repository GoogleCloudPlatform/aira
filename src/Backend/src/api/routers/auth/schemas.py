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
Module containing schemas for all auth endpoints
"""
import datetime
import typing
import uuid

import pydantic


class FirebaseLogin(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    token: str


class EmailPasswordLogin(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    email_address: str
    password: str


class Session(pydantic.BaseModel):
    """
    Schema related to the login request.
    """

    id: uuid.UUID
    user_name: str
    token_type: typing.Literal["bearer"] = "bearer"
    access_token: str
    refresh_token: str
    expires_in: datetime.timedelta
    scopes: list[str]
