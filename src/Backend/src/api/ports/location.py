"""
Module related to the port of location repository.
"""

import abc
import uuid

from api import models, typings


class CountryRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, country_id: uuid.UUID) -> models.Country:
        pass

    @abc.abstractmethod
    async def create(self, country_model: models.Country) -> models.Country:
        pass

    @abc.abstractmethod
    async def delete(self, country_model: models.Country) -> None:
        pass

    @abc.abstractmethod
    async def list(self) -> list[models.Country]:
        pass


class StateRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, state_id: uuid.UUID) -> models.State:
        pass

    @abc.abstractmethod
    async def create(self, state_model: models.State) -> models.State:
        pass

    @abc.abstractmethod
    async def delete(self, state_model: models.State) -> None:
        pass

    @abc.abstractmethod
    async def list(self, country_id: uuid.UUID | None = None) -> list[models.State]:
        pass


class CityRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, city_id: uuid.UUID) -> models.City:
        pass

    @abc.abstractmethod
    async def create(self, city_model: models.City) -> models.City:
        pass

    @abc.abstractmethod
    async def delete(self, city_model: models.City) -> None:
        pass

    @abc.abstractmethod
    async def list(self, state_id: uuid.UUID | None = None) -> list[models.City]:
        pass


class GetCountry(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, country_id: uuid.UUID) -> models.Country:
        pass


class ListCountries(abc.ABC):
    @abc.abstractmethod
    async def __call__(
        self, page_size: int = 10, page: int = 1, query: str | None = None
    ) -> tuple[list[models.Country], typings.PaginationMetadata]:
        pass


class GetState(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, state_id: uuid.UUID) -> models.State:
        pass


class ListStates(abc.ABC):
    @abc.abstractmethod
    async def __call__(
        self,
        country_id: uuid.UUID | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.State], typings.PaginationMetadata]:
        pass


class GetCity(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, city_id: uuid.UUID) -> models.City:
        pass


class ListCities(abc.ABC):
    @abc.abstractmethod
    async def __call__(
        self,
        state_id: uuid.UUID | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.City], typings.PaginationMetadata]:
        pass
