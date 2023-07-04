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
Module related to the port of any external auth.
"""
import abc
import uuid

from api import models, typings


# pylint: disable=too-few-public-methods
class UserRepository(abc.ABC):
    """
    User repository implementation that returns user data.
    """

    @abc.abstractmethod
    async def get(
        self,
        user_id: uuid.UUID | None = None,
        external_id: str | None = None,
        email: str | None = None,
    ) -> models.User:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        user_model: models.User,
    ) -> models.User:
        """
        Creates and return the user model.

        :param user_model: the user model parameter.
        """

    @abc.abstractmethod
    async def delete(self, user_model: models.User) -> None:
        """
        Method to delete a user.

        :param user_model: the user model parameter.
        """


class ListUsers(abc.ABC):
    """
    Query to get all users.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        roles: list[uuid.UUID] | None = None,
        groups: list[uuid.UUID] | None = None,
        organizations: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.User], typings.PaginationMetadata]:
        """
        Method to list all users.
        """


class GetUser(abc.ABC):
    """
    Query to get a specific user.
    """

    @abc.abstractmethod
    async def __call__(self, user_id: uuid.UUID) -> models.User:
        """
        Method to get a specific user.

        :param user_id: the user identifier.
        """


class CheckUserOnGroup(abc.ABC):
    """
    Query to check if any user is on a group.
    """

    @abc.abstractmethod
    async def __call__(self, group_id: uuid.UUID) -> bool:
        """
        Method to check if user on group.

        :param group_id: the group identifier.
        """
