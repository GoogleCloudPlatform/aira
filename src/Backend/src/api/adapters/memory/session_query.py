# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module for all session related sqlalchemy memory implementation queries.
"""
import uuid

from api import errors, models, ports


class SessionRepository(ports.SessionRepository):
    """
    Session repository memory implementation that returns session data.
    """

    def __init__(self, items: list[models.Session] | None = None) -> None:
        self._items = items if items else []

    async def get(
        self,
        session_id: uuid.UUID,
    ) -> models.Session:
        """
        Get session by params.

        :params session_id: session id on database.
        """
        if self._items:
            items = self._items
            items = [item for item in items if item.id == session_id]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(self, session_model: models.Session) -> models.Session:
        """
        Method to create a session for the user.

        :param session_model: the session model parameter.

        :returns: session model.
        """
        if any(item for item in self._items if item.id == session_model.id):
            raise errors.AlreadyExists()
        self._items.append(session_model)
        return session_model

    async def delete(self, session_model: models.Session) -> None:
        """
        Method to delete a session from a user.

        :param session_model: the session model parameter.
        """
        self._items.remove(session_model)
