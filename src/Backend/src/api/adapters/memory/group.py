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
Module for all group related sqlalchemy memory implementation queries.
"""
import uuid

from api import errors, models, ports, typings
from api.helpers import time_now


class GroupRepository(ports.GroupRepository):
    """
    Group repository memory implementation that returns group data.
    """

    def __init__(self, items: list[models.Group] | None = None) -> None:
        self._items = items if items else []

    async def get(
        self,
        group_id: uuid.UUID,
    ) -> models.Group:
        """
        Get group by params.

        :params group_id: group id on database.
        """
        if self._items:
            items = self._items
            items = [item for item in items if item.id == group_id]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(self, group_model: models.Group) -> models.Group:
        """
        Method to create a group for the user.

        :param group_model: the group model parameter.

        :returns: group model.
        """
        if any(item for item in self._items if item.id == group_model.id):
            raise errors.AlreadyExists()
        group_model.created_at = group_model.updated_at = time_now()
        org = models.Organization(
            name="fake",
            city="fake",
            state="fk",
            customer_id="fake",
            region="fake",
        )
        org.id = group_model.organization_id
        group_model.organization = org
        self._items.append(group_model)
        return group_model

    async def delete(self, group_model: models.Group) -> None:
        """
        Method to delete a group.

        :param group_model: the group model parameter.
        """
        self._items = [item for item in self._items if item.id != group_model.id]


class GetGroup(ports.GetGroup):
    """
    Query to get a specific group.
    """

    def __init__(self, groups: list[models.Group] | None = None) -> None:
        self._items = groups if groups else []

    async def __call__(self, group_id: uuid.UUID) -> models.Group:
        """
        Method to get a specific group.

        :param group_id: the group identifier.
        """
        items = self._items
        orgs = [item for item in items if item.id == group_id]
        if len(orgs) != 1:
            raise errors.NotFound()
        return orgs[0]


class ListGroups(ports.ListGroups):
    """
    Query to get all groups.
    """

    def __init__(self, groups: list[models.Group] | None = None) -> None:
        self._items = groups if groups else []
        self.called = 0

    async def __call__(
        self,
        groups: list[uuid.UUID] | None = None,
        shift: str | None = None,
        grade: models.Grades | None = None,
        organizations: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.Group], typings.PaginationMetadata]:
        """
        Method to list all groups.
        """
        self.called += 1
        items = self._items
        if groups is not None:
            items = [item for item in items if item.id in groups]
        if shift:
            items = [item for item in items if item.shift == shift]
        if grade:
            items = [item for item in items if item.grade == grade]
        if organizations:
            items = [item for item in items if item.organization_id in organizations]
        if query:
            items = [
                item
                for item in items
                if query.lower() in item.name.lower()
                or query.lower() in item.grade.lower()
                or query.lower() in item.shift.lower()
                or query.lower() in item.organization.name.lower()
            ]
        return items[
            (page - 1) * page_size : page * page_size
        ], typings.PaginationMetadata(
            current_page=page,
            total_pages=len(items) // page_size,
            page_size=page_size,
            total_items=len(self._items),
        )


class CheckGroupOnOrg(ports.CheckGroupOnOrg):
    """
    Query to check if any group is on an org.
    """

    def __init__(self, groups: list[models.Group] | None = None) -> None:
        self._items = groups if groups else []
        self.called = 0

    async def __call__(self, organization_id: uuid.UUID) -> bool:
        """
        Method to check if group is on any org.

        :param organization_id: the org identifier.
        """
        items = self._items

        items = [item for item in items if item.organization_id == organization_id]
        if any(items):
            return True
        return False
