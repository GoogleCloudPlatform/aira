"""
Module related to the port of any external auth.
"""

import abc
import uuid

from api import models, typings


# pylint: disable=too-few-public-methods
class UserRepository(abc.ABC):
    """
    User repository implementation that returns user data.
    """

    @abc.abstractmethod
    async def get(
        self,
        user_id: uuid.UUID | None = None,
        external_id: str | None = None,
        email: str | None = None,
        reset_token: str | None = None,
    ) -> models.User:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        user_model: models.User,
    ) -> models.User:
        """
        Creates and return the user model.

        :param user_model: the user model parameter.
        """

    @abc.abstractmethod
    async def delete(self, user_model: models.User) -> None:
        """
        Method to delete a user.

        :param user_model: the user model parameter.
        """

    @abc.abstractmethod
    async def create_or_update_student(
        self,
        student: typings.CreateOrUpdateUser,
        group_customer_id: str,
        updated_groups: dict[str, models.Group],
        cached_users: list[models.User],
    ) -> models.User | None:
        """
        Method to create or update a list of student filtering by customer id.

        :param student: student to insert or update.
        :param group_customer_id: group customer id to filter.
        """

    @abc.abstractmethod
    async def create_or_update_professor(
        self,
        professor: typings.CreateOrUpdateUser,
        groups_customer_id: list[str],
        organizations_customer_id: list[str],
        updated_organizations: dict[str, models.Organization],
        updated_groups: dict[str, models.Group],
        cached_profs: list[models.User],
    ) -> models.User | None:
        """
        Method to create or update a list of professor
        filtering by customer id and email.

        :param professor: professor to insert or update.
        :param group_customer_id: group customer id to filter.
        """

    @abc.abstractmethod
    async def list(
        self,
        user_ids: list[uuid.UUID] | None = None,
        customer_ids: list[str] | None = None,
    ) -> list[models.User]:
        """
        Method to facilitate user import and list users based on an id list.

        :param user_ids: array with user ids.
        """


class ListUsers(abc.ABC):
    """
    Query to get all users.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        roles: list[uuid.UUID] | None = None,
        groups: list[uuid.UUID] | None = None,
        organizations: list[uuid.UUID] | None = None,
        page_size: int = 10,
        page: int = 1,
        query: str | None = None,
    ) -> tuple[list[models.User], typings.PaginationMetadata]:
        """
        Method to list all users.
        """


class ListUsersWithExams(abc.ABC):
    """
    Query to get all users.
    """

    @abc.abstractmethod
    async def __call__(
        self,
        groups: list[uuid.UUID],
        organizations: list[uuid.UUID],
        role_ids: list[uuid.UUID] | None = None,
        query: str | None = None,
        show_finished: bool = True,
        page_size: int = 10,
        page: int = 1,
    ) -> tuple[list[dict], typings.PaginationMetadata]:  # type:ignore[type-arg]
        """
        Method to list all users with exams.
        """


class GetUser(abc.ABC):
    """
    Query to get a specific user.
    """

    @abc.abstractmethod
    async def __call__(self, user_id: uuid.UUID) -> models.User:
        """
        Method to get a specific user.

        :param user_id: the user identifier.
        """


class CheckUserOnGroup(abc.ABC):
    """
    Query to check if any user is on a group.
    """

    @abc.abstractmethod
    async def __call__(self, group_id: uuid.UUID) -> bool:
        """
        Method to check if user on group.

        :param group_id: the group identifier.
        """


class ListPersonifiableUsers(abc.ABC):
    """
    List users that a user can impersonate.
    """

    @abc.abstractmethod
    async def __call__(self, groups: list[uuid.UUID]) -> list[models.User]:
        """
        Method to list users that a user can impersonate.

        :param groups: list of identifier for groups.

        :returns: list of users that can be impersonated.
        """
