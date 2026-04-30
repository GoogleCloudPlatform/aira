import abc
import uuid
from api import models, typings

class ListShifts(abc.ABC):
    @abc.abstractmethod
    async def __call__(
        self,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.WorkShift], typings.PaginationMetadata]:
        raise NotImplementedError

class GetShift(abc.ABC):
    @abc.abstractmethod
    async def __call__(self, shift_id: uuid.UUID) -> models.WorkShift:
        raise NotImplementedError

class WorkShiftRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, shift_id: uuid.UUID) -> models.WorkShift:
        raise NotImplementedError

    @abc.abstractmethod
    async def create(self, shift: models.WorkShift) -> models.WorkShift:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, shift: models.WorkShift) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def list(self, shift_ids: list[uuid.UUID] | None = None) -> list[models.WorkShift]:
        raise NotImplementedError
