"""
Module related to the port of the session repository.
"""

from __future__ import annotations

import abc
import typing


class DataSyncApi(abc.ABC):
    """
    Session repository.
    """

    @abc.abstractmethod
    async def list_group(self) -> list[dict[str, typing.Any]]:
        """
        Method get the list of groups to be synced.

        :returns: list of dictionary.
        """

    @abc.abstractmethod
    async def list_organization(self) -> list[dict[str, typing.Any]]:
        """
        Method get the list of organizations to be synced.

        :returns: list of dictionary.
        """

    @abc.abstractmethod
    async def list_student(self) -> list[dict[str, typing.Any]]:
        """
        Method get the list of students to be synced.

        :returns: list of dictionary.
        """

    @abc.abstractmethod
    async def list_student_paginated(self, index: int) -> typing.Any:
        """
        Method get the list of students to be synced given an index.

        :returns: list of dictionary.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def list_professor(self) -> list[dict[str, typing.Any]]:
        """
        Method get the list of professors to be synced.

        :returns: list of dictionary.
        """
