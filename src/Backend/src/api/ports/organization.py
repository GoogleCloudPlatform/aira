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
