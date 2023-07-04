"""
Module for all organization related sqlalchemy memory implementation queries.
"""
import uuid

from api import errors, models, ports, typings
from api.helpers import time_now


class OrganizationRepository(ports.OrganizationRepository):
    """
    Organization repository memory implementation that returns organization data.
    """

    def __init__(self, items: list[models.Organization] | None = None) -> None:
        self._items = items if items else []

    async def get(
        self,
        organization_id: uuid.UUID,
    ) -> models.Organization:
        """
        Get organization by params.

        :params organization_id: organization id on database.
        """
        if self._items:
            items = self._items
            items = [item for item in items if item.id == organization_id]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(
        self, organization_model: models.Organization
    ) -> models.Organization:
        """
        Method to create a organization for the user.

        :param organization_model: the organization model parameter.

        :returns: organization model.
        """
        if any(item for item in self._items if item.id == organization_model.id):
            raise errors.AlreadyExists()
        organization_model.created_at = organization_model.updated_at = time_now()
        self._items.append(organization_model)
        return organization_model

    async def delete(self, organization_model: models.Organization) -> None:
        """
        Method to delete a organization.

        :param organization_model: the organization model parameter.
        """
        self._items = [item for item in self._items if item.id != organization_model.id]


class GetOrganization(ports.GetOrganization):
    """
    Query to get a specific organization.
    """

    def __init__(self, organizations: list[models.Organization] | None = None) -> None:
        self._items = organizations if organizations else []

    async def __call__(self, organization_id: uuid.UUID) -> models.Organization:
        """
        Method to get a specific organization.

        :param organization_id: the organization identifier.
        """
        items = self._items
        orgs = [item for item in items if item.id == organization_id]
        if len(orgs) != 1:
            raise errors.NotFound()
        return orgs[0]


class ListOrganizations(ports.ListOrganizations):
    """
    Query to get all organizations.
    """

    def __init__(self, organizations: list[models.Organization] | None = None) -> None:
        self._items = organizations if organizations else []
        self.called = 0

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
        items = self._items
        self.called += 1
        if city:
            items = [item for item in items if item.city == city]
        if organizations:
            items = [item for item in items if item.id in organizations]
        if query:
            items = [
                item
                for item in items
                if query in item.city
                or query in item.name
                or (item.region and query in item.region)
            ]
        return items[
            (page - 1) * page_size : page * page_size
        ], typings.PaginationMetadata(
            current_page=page,
            total_pages=len(items) // page_size,
            page_size=page_size,
            total_items=len(self._items),
        )
