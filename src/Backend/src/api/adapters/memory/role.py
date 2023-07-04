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
Module for all role related sqlalchemy memory implementation queries.
"""
import uuid

from api import errors, models, ports, typings
from api.helpers import time_now


class RoleRepository(ports.RoleRepository):
    """
    Role repository memory implementation that returns role data.
    """

    def __init__(self, items: list[models.Role] | None = None) -> None:
        self._items = items if items else []

    async def get(
        self, role_id: uuid.UUID | None = None, name: str | None = None
    ) -> models.Role:
        """
        Get role by params.

        :params role_id: role id on database.
        :params name: name on database.
        """
        if self._items:
            items = self._items
            if role_id:
                items = [item for item in items if item.id == role_id]
            if name:
                items = [item for item in items if item.name == name]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(self, role_model: models.Role) -> models.Role:
        """
        Method to create a role for the role.

        :param role_model: the role model parameter.

        :returns: role model.
        """
        if any(item for item in self._items if item.id == role_model.id):
            raise errors.AlreadyExists()
        role_model.created_at = role_model.updated_at = time_now()
        self._items.append(role_model)
        return role_model

    async def delete(self, role_model: models.Role) -> None:
        """
        Method to delete a role.

        :param role_model: the role model parameter.
        """
        self._items = [item for item in self._items if item.id != role_model.id]


class ListRoles(ports.ListRoles):
    """
    Query to get all roles.
    """

    def __init__(self, roles: list[models.Role] | None = None) -> None:
        self._items = roles if roles else []
        self.called = 0

    async def __call__(
        self,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[models.Role], typings.PaginationMetadata]:
        """
        Method to list all roles.
        """
        items = self._items
        self.called += 1

        return items[
            (page - 1) * page_size : page * page_size
        ], typings.PaginationMetadata(
            current_page=page,
            total_pages=len(items) // page_size,
            page_size=page_size,
            total_items=len(self._items),
        )


class GetRole(ports.GetRole):
    """
    Query to get a specific role.
    """

    def __init__(self, roles: list[models.Role] | None = None) -> None:
        self._items = roles if roles else []

    async def __call__(self, role_id: uuid.UUID) -> models.Role:
        """
        Method to get a specific role.

        :param role_id: the role identifier.
        """
        items = self._items
        roles = [item for item in items if item.id == role_id]
        if len(roles) != 1:
            raise errors.NotFound()
        return roles[0]
