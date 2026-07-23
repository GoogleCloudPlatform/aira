import abc
import uuid

from api import models, typings


class KnowledgeBaseRepository(abc.ABC):
    """
    Interface for mutating and fetching individual knowledge base files.
    """

    @abc.abstractmethod
    async def get(
        self,
        file_id: uuid.UUID,
    ) -> models.KnowledgeBaseFile | None:
        """
        Retrieve a knowledge base file record by its UUID.
        """

    @abc.abstractmethod
    async def create(
        self,
        file_model: models.KnowledgeBaseFile,
    ) -> models.KnowledgeBaseFile:
        """
        Create a new knowledge base file record.
        """

    @abc.abstractmethod
    async def delete(
        self,
        file_model: models.KnowledgeBaseFile,
    ) -> None:
        """
        Delete a knowledge base file record.
        """


class ListKnowledgeBaseFiles(abc.ABC):
    """
    Query interface to list and paginate knowledge base files.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[models.KnowledgeBaseFile], typings.PaginationMetadata]:
        """
        List and paginate all knowledge base files.
        """
