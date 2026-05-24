import abc
import uuid

from api import models


class TutorialRepository(abc.ABC):
    @abc.abstractmethod
    async def get(self, tutorial_id: uuid.UUID) -> models.Tutorial:
        pass

    @abc.abstractmethod
    async def create(self, tutorial_model: models.Tutorial) -> models.Tutorial:
        pass

    @abc.abstractmethod
    async def delete(self, tutorial_model: models.Tutorial) -> None:
        pass

    @abc.abstractmethod
    async def get_latest_by_audience(self, audience: str) -> models.Tutorial | None:
        pass
