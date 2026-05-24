"""
Module for all location related sqlalchemy queries.
"""

from __future__ import annotations

import logging
import uuid

import sqlalchemy as sa
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import exc
from sqlalchemy.ext import asyncio as sqlalchemy_aio
from sqlalchemy.orm import joinedload

from api import errors, models, ports, typings

logger = logging.getLogger(__name__)


class CountryRepository(ports.CountryRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, country_id: uuid.UUID) -> models.Country:
        stmt = sa.select(models.Country).where(models.Country.id == country_id)
        result = await self._session.execute(stmt)
        if not (country := result.scalars().one_or_none()):
            raise errors.NotFound()
        return country

    async def create(self, country_model: models.Country) -> models.Country:
        self._session.add(country_model)
        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception
        return country_model

    async def delete(self, country_model: models.Country) -> None:
        await self._session.delete(country_model)

    async def list(self) -> list[models.Country]:
        stmt = sa.select(models.Country).order_by(models.Country.name.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())


class StateRepository(ports.StateRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, state_id: uuid.UUID) -> models.State:
        stmt = sa.select(models.State).where(models.State.id == state_id)
        result = await self._session.execute(stmt)
        if not (state := result.scalars().one_or_none()):
            raise errors.NotFound()
        return state

    async def create(self, state_model: models.State) -> models.State:
        self._session.add(state_model)
        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception
        return state_model

    async def delete(self, state_model: models.State) -> None:
        await self._session.delete(state_model)

    async def list(self, country_id: uuid.UUID | None = None) -> list[models.State]:
        stmt = sa.select(models.State).order_by(models.State.name.asc())
        if country_id:
            stmt = stmt.where(models.State.country_id == country_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())


class CityRepository(ports.CityRepository):
    def __init__(self, session: sqlalchemy_aio.AsyncSession) -> None:
        self._session = session

    async def get(self, city_id: uuid.UUID) -> models.City:
        stmt = sa.select(models.City).where(models.City.id == city_id)
        result = await self._session.execute(stmt)
        if not (city := result.scalars().one_or_none()):
            raise errors.NotFound()
        return city

    async def create(self, city_model: models.City) -> models.City:
        self._session.add(city_model)
        try:
            await self._session.flush()
        except exc.IntegrityError as exception:
            raise errors.AlreadyExists() from exception
        return city_model

    async def delete(self, city_model: models.City) -> None:
        await self._session.delete(city_model)

    async def list(self, state_id: uuid.UUID | None = None) -> list[models.City]:
        stmt = (
            sa.select(models.City)
            .options(joinedload(models.City.state))
            .order_by(models.City.name.asc())
        )
        if state_id:
            stmt = stmt.where(models.City.state_id == state_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique())


class ListCountries(ports.ListCountries):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self, page_size: int = 10, page: int = 1, query: str | None = None
    ) -> tuple[list[models.Country], typings.PaginationMetadata]:
        stmt = sa.select(models.Country).order_by(models.Country.name.asc())
        if query:
            stmt = stmt.where(models.Country.name.ilike(f"%{query}%"))

        async with self._session_factory() as session:
            params = Params(page=page, size=page_size)
            result: typings.Paginated = await paginate(
                session, stmt, params=params, unique=True
            )

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class ListStates(ports.ListStates):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        country_id: uuid.UUID | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.State], typings.PaginationMetadata]:
        stmt = (
            sa.select(models.State)
            .options(joinedload(models.State.country))
            .order_by(models.State.name.asc())
        )
        if country_id:
            stmt = stmt.where(models.State.country_id == country_id)
        if query:
            stmt = stmt.where(models.State.name.ilike(f"%{query}%"))

        async with self._session_factory() as session:
            params = Params(page=page, size=page_size)
            result: typings.Paginated = await paginate(
                session, stmt, params=params, unique=True
            )

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class ListCities(ports.ListCities):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(
        self,
        state_id: uuid.UUID | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.City], typings.PaginationMetadata]:
        stmt = (
            sa.select(models.City)
            .options(joinedload(models.City.state))
            .order_by(models.City.name.asc())
        )
        if state_id:
            stmt = stmt.where(models.City.state_id == state_id)
        if query:
            stmt = stmt.where(models.City.name.ilike(f"%{query}%"))

        async with self._session_factory() as session:
            params = Params(page=page, size=page_size)
            result: typings.Paginated = await paginate(
                session, stmt, params=params, unique=True
            )

        return result.items, typings.PaginationMetadata(
            current_page=result.page,
            total_pages=result.pages,
            total_items=result.total,
            page_size=result.size,
        )


class GetCountry(ports.GetCountry):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, country_id: uuid.UUID) -> models.Country:
        stmt = sa.select(models.Country).where(models.Country.id == country_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            if not (country := result.scalars().one_or_none()):
                raise errors.NotFound()
            return country


class GetState(ports.GetState):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, state_id: uuid.UUID) -> models.State:
        stmt = (
            sa.select(models.State)
            .options(joinedload(models.State.country))
            .where(models.State.id == state_id)
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            if not (state := result.scalars().one_or_none()):
                raise errors.NotFound()
            return state


class GetCity(ports.GetCity):
    def __init__(self, session_factory: typings.SessionFactory):
        self._session_factory = session_factory

    async def __call__(self, city_id: uuid.UUID) -> models.City:
        stmt = (
            sa.select(models.City)
            .options(joinedload(models.City.state))
            .where(models.City.id == city_id)
        )
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            if not (city := result.scalars().one_or_none()):
                raise errors.NotFound()
            return city
