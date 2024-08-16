"""
Module related to the port of organization repository.
"""

import abc
import uuid

from api import models, typings


# pylint: disable=too-few-public-methods
class OrganizationRepository(abc.ABC):
    """
    Group repository that returns group data.
    """

    @abc.abstractmethod
    async def get(
        self,
        organization_id: uuid.UUID,
    ) -> models.Organization:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        organization_model: models.Organization,
    ) -> models.Organization:
        """
        Creates and return the organization model.

        :param organization_model: the organization model parameter.
        """

    @abc.abstractmethod
    async def delete(self, organization_model: models.Organization) -> None:
        """
        Method to delete a organization.

        :param organization_model: the organization model parameter.
        """

    @abc.abstractmethod
    async def create_or_update(
        self,
        sync_org: typings.CreateOrUpdateOrganization,
        cached_orgs: list[models.Organization],
    ) -> models.Organization:
        """
        Method to create or update a list of organization filtering by customer id.

        :param sync_org: sync_org to insert or update.
        """

    @abc.abstractmethod
    async def list(
        self,
        org_ids: list[uuid.UUID] | None = None,
        customer_ids: list[str] | None = None,
    ) -> list[models.Organization]:
        """
        Method to list orgs.

        :param org_ids: parameter with array of ids.
        :param customer_ids: parameter with array of customer ids.
        """


class GetOrganization(abc.ABC):
    """
    Query to get a specific org.
    """

    @abc.abstractmethod
    async def __call__(self, organization_id: uuid.UUID) -> models.Organization:
        """
        Method to get a specific org.

        :param organization_id: the org identifier.
        """


class ListOrganizations(abc.ABC):
    """
    Query to get all organizations.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        city: str | None = None,
        organizations: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.Organization], typings.PaginationMetadata]:
        """
        Method to list all orgs.
        """


class ListOrganizationUtils(abc.ABC):
    """
    Query to list unique state/county/region from orgs.
    """

    @abc.abstractmethod
    async def __call__(
        self,
    ) -> dict[str, list[str]]:
        """
        Method to list unique state/county/region from orgs.
        """
