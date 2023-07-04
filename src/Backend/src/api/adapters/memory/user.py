"""
Module for all user related sqlalchemy memory implementation queries.
"""
import uuid

from api import errors, models, ports, typings
from api.helpers import time_now


class UserRepository(ports.UserRepository):
    """
    User repository memory implementation that returns user data.
    """

    def __init__(self, items: list[models.User] | None = None) -> None:
        self._items = items if items else []

    async def get(
        self,
        user_id: uuid.UUID | None = None,
        external_id: str | None = None,
        email: str | None = None,
    ) -> models.User:
        """
        Get user by params.

        :params user_id: user id on database.
        :params external_id: user id provided by firebase.
        """
        if self._items:
            items = self._items
            if user_id:
                items = [item for item in items if item.id == user_id]
            if external_id:
                items = [item for item in items if item.external_id == external_id]
            if email:
                items = [item for item in items if item.email_address == email]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(self, user_model: models.User) -> models.User:
        """
        Method to create a user for the user.

        :param user_model: the user model parameter.

        :returns: user model.
        """
        if any(item for item in self._items if item.id == user_model.id):
            raise errors.AlreadyExists()
        user_model.created_at = user_model.updated_at = time_now()
        role = models.Role(
            description={}, display_name={}, name="fake role", scopes=["*"]
        )
        role.id = user_model.role_id
        user_model.role = role
        self._items.append(user_model)
        return user_model

    async def delete(self, user_model: models.User) -> None:
        """
        Method to delete a user.

        :param user_model: the user model parameter.
        """
        self._items = [item for item in self._items if item.id != user_model.id]


class ListUsers(ports.ListUsers):
    """
    Query to get all users.
    """

    def __init__(self, users: list[models.User] | None = None) -> None:
        self._items = users if users else []
        self.called = 0

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
        items = self._items
        self.called += 1
        if roles:
            items = [item for item in items if item.role_id in roles]
        if groups:
            items = [
                item
                for item in items
                if any(group.id in groups for group in item.groups)
            ]
        if organizations:
            items = [
                item
                for item in items
                if any(group.organization_id in organizations for group in item.groups)
            ]
        if query:
            items = [
                item
                for item in items
                if query in item.email_address
                or query in item.name
                or any(query in group.name for group in item.groups)
                or any(
                    query in organization.name for organization in item.organizations
                )
            ]

        return items[
            (page - 1) * page_size : page * page_size
        ], typings.PaginationMetadata(
            current_page=page,
            total_pages=len(items) // page_size,
            page_size=page_size,
            total_items=len(self._items),
        )


class GetUser(ports.GetUser):
    """
    Query to get a specific user.
    """

    def __init__(self, users: list[models.User] | None = None) -> None:
        self._items = users if users else []

    async def __call__(self, user_id: uuid.UUID) -> models.User:
        """
        Method to get a specific user.

        :param user_id: the user identifier.
        """
        items = self._items
        users = [item for item in items if item.id == user_id]
        if len(users) != 1:
            raise errors.NotFound()
        return users[0]


class CheckUserOnGroup(ports.CheckUserOnGroup):
    """
    Query to check if any user is on a group.
    """

    def __init__(self, users: list[models.User] | None = None) -> None:
        self._items = users if users else []

    async def __call__(self, group_id: uuid.UUID) -> bool:
        """
        Method to check if user on group.

        :param group_id: the group identifier.
        """

        items = self._items
        users = [
            item for item in items if any(group.id == group_id for group in item.groups)
        ]

        if any(users):
            return True
        return False
