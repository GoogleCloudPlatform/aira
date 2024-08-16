"""
Module related to the port of group repository.
"""

import abc
import uuid

from api import models, typings


# pylint: disable=too-few-public-methods
class GroupRepository(abc.ABC):
    """
    Group repository that returns group data.
    """

    @abc.abstractmethod
    async def get(
        self,
        group_id: uuid.UUID,
    ) -> models.Group:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        group_model: models.Group,
    ) -> models.Group:
        """
        Creates and return the group model.
        """

    @abc.abstractmethod
    async def delete(self, group_model: models.Group) -> None:
        """
        Method to delete a group.

        :param group_model: the group model parameter.
        """

    @abc.abstractmethod
    async def create_or_update(
        self,
        sync_group: typings.CreateOrUpdateGroup,
        org_customer_id: str,
        updated_orgs: dict[str, models.Organization],
        cached_groups: list[models.Group],
    ) -> models.Group | None:
        """
        Method to create or update a list of group filtering by customer id.

        :param sync_group: group to insert or update.
        :param org_customer_id: org customer id search.
        """

    @abc.abstractmethod
    async def list(
        self,
        group_ids: list[uuid.UUID] | None = None,
        customer_ids: list[str] | None = None,
    ) -> list[models.Group]:
        """
        Method to list groups.

        :param group_ids: parameter with array of ids.
        """


class GetGroup(abc.ABC):
    """
    Query to get a specific group.
    """

    @abc.abstractmethod
    async def __call__(self, group_id: uuid.UUID) -> models.Group:
        """
        Method to get a specific group.

        :param group_id: the group identifier.
        """


class ListGroups(abc.ABC):
    """
    Query to get all groups.
    """

    @abc.abstractmethod
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


class ListGroupsWithoutOrg(abc.ABC):
    """
    Query to get all groups without bringing org.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        groups: list[uuid.UUID] | None = None,
        shift: str | None = None,
        grade: str | None = None,
    ) -> list[models.Group]:
        """
        Method to list all groups.
        """


class CheckGroupOnOrg(abc.ABC):
    """
    Query to check if any group is on an org.
    """

    @abc.abstractmethod
    async def __call__(self, organization_id: uuid.UUID) -> bool:
        """
        Method to check if group is on any org.

        :param organization_id: the org identifier.
        """
