"""
Module related to the port of any external auth.
"""

import abc
import uuid

from api import models, typings


# pylint: disable=too-few-public-methods
class RoleRepository(abc.ABC):
    """
    Role repository implementation that returns role data.
    """

    @abc.abstractmethod
    async def get(
        self, role_id: uuid.UUID | None = None, name: str | None = None
    ) -> models.Role:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        role_model: models.Role,
    ) -> models.Role:
        """
        Creates and return the role model.

        :param role_model: the role model parameter.
        """

    @abc.abstractmethod
    async def delete(self, role_model: models.Role) -> None:
        """
        Method to delete a role.

        :param role_model: the role model parameter.
        """


class GetRoleByName(abc.ABC):
    """
    Get role by its name.
    """

    @abc.abstractmethod
    async def __call__(self, name: str) -> models.Role:
        """
        Method to get a specific role.

        :param role_name: the role name.
        """


class ListRoles(abc.ABC):
    """
    Query to get all roles.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        scope: str | None = None,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[models.Role], typings.PaginationMetadata]:
        """
        Method to list all roles.
        """


class GetRole(abc.ABC):
    """
    Query to get a specific role.
    """

    @abc.abstractmethod
    async def __call__(self, role_id: uuid.UUID) -> models.Role:
        """
        Method to get a specific role.

        :param role_id: the role identifier.
        """
