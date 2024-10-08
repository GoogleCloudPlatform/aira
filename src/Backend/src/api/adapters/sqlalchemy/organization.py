"""
Module for all user related sqlalchemy queries.
"""

from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import errors, models, ports, typings

logger = logging.getLogger(__name__)


class OrganizationRepository(ports.OrganizationRepository):
    """
    Organization repository implementation that returns organization data.
    """

    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, organization_id: uuid.UUID) -> models.Organization:
        """
        Get organization by params.

        :param organization_id: organization id on database.
        """
        stmt = sa.select(models.Organization).where(
            models.Organization.id == organization_id
        )

        result = await self._session.execute(stmt)
        if not (organization := result.scalars().one_or_none()):
            raise errors.NotFound()

        return organization

    async def create(
        self, organization_model: models.Organization
    ) -> models.Organization:
        """
        Method to create a organization.

        :param organization_model: the organization model parameter.

        :returns: organization model.

        :raises errors.AlreadyExists: if the entity is duplicated.
        """
        self._session.add(organization_model)

        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception

        return organization_model

    async def delete(self, organization_model: models.Organization) -> None:
        """
        Method to delete a organization.

        :param organization_model: the organization model parameter.
        """
        await self._session.delete(organization_model)

    async def create_or_update(
        self,
        sync_org: typings.CreateOrUpdateOrganization,
        cached_orgs: list[models.Organization],
    ) -> models.Organization:
        """
        Method to create or update a list of organization filtering by customer id.

        :param sync_org: sync_org to insert or update.
        """
        organization = next(
            (org for org in cached_orgs if org.customer_id == sync_org.customer_id),
            None,
        )

        if organization:
            organization.name = sync_org.name
            organization.region = sync_org.region
            organization.city = sync_org.city
            organization.state = sync_org.state
            organization.county = sync_org.county
        else:
            organization = models.Organization(
                customer_id=sync_org.customer_id,
                name=sync_org.name,
                region=sync_org.region,
                city=sync_org.city,
                state=sync_org.state,
                county=sync_org.county,
            )
            self._session.add(organization)

        return organization

    async def list(
        self,
        org_ids: list[uuid.UUID] | None = None,
        customer_ids: list[str] | None = None,
    ) -> list[models.Organization]:
        """
        Method to list orgs.

        :param org_ids: parameter with array of ids.
        """
        stmt = sa.select(models.Organization)
        if org_ids:
            stmt = stmt.where(models.Organization.id.in_(org_ids))
        if customer_ids:
            stmt = stmt.where(models.Organization.customer_id.in_(customer_ids))
        result = await self._session.execute(stmt)
        orgs = list(result.scalars().unique())
        return orgs


class ListOrganizations(ports.ListOrganizations):
    """
    Query to get all organizations.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

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
        org = models.Organization
        stmt = sa.select(org).order_by(org.updated_at.desc())

        if city:
            stmt = stmt.where(org.city == city)

        if organizations is not None:
            stmt = stmt.where(org.id.in_(organizations))

        if query:
            stmt = stmt.where(
                sa.or_(
                    org.city.ilike(f"%{query}%"),
                    org.name.ilike(f"%{query}%"),
                    org.region.ilike(f"%{query}%"),
                )
            )

        async with self._session_factory() as session:
            if page_size >= 0:
                params = Params(page=page, size=page_size)
                result: typings.Paginated = await paginate(
                    session, stmt, params=params, unique=True
                )
            else:
                result_all = await session.execute(stmt)
                organization_result = list(result_all.scalars().unique())
                return organization_result, typings.PaginationMetadata(
                    current_page=1,
                    total_pages=1,
                    total_items=len(organization_result),
                    page_size=len(organization_result),
                )
        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class GetOrganization(ports.GetOrganization):
    """
    Query to get a specific organization.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, organization_id: uuid.UUID) -> models.Organization:
        """
        Method to get a specific organization.

        :param organization_id: the organization identifier.
        """

        stmt = sa.select(models.Organization).where(
            models.Organization.id == organization_id
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)

        if not (organization := result.scalars().one_or_none()):
            raise errors.NotFound()

        return organization


class ListOrganizationUtils(ports.ListOrganizationUtils):
    """
    Query to list unique state/county/region from orgs.
    """

    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
    ) -> dict[str, list[str]]:
        county = sa.select(sa.distinct(models.Organization.county))
        state = sa.select(sa.distinct(models.Organization.state))
        region = sa.select(sa.distinct(models.Organization.region))
        async with self._session_factory() as session:
            result_county = await session.execute(county)
            result_state = await session.execute(state)
            result_region = await session.execute(region)
        return {
            "county": list(result_county.scalars().all()),
            "state": list(result_state.scalars().all()),
            "region": list(result_region.scalars().all()),  # type: ignore[arg-type]
        }
