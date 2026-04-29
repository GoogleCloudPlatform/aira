import abc
import uuid
from api import models, typings

class SeriesRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, series_id: uuid.UUID) -> models.Series:
        pass

    @abc.abstractmethod
    async def create(self, series_model: models.Series) -> models.Series:
        pass

    @abc.abstractmethod
    async def delete(self, series_model: models.Series) -> None:
        pass

    @abc.abstractmethod
    async def list(self) -> list[models.Series]:
        pass

class ListSeries(abc.ABC):
    @abc.abstractmethod
    async def __call__(
        self, page_size: int = 10, page: int = 1, query: str | None = None
    ) -> tuple[list[models.Series], typings.PaginationMetadata]:
        pass

class GetSeries(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, series_id: uuid.UUID) -> models.Series:
        pass
