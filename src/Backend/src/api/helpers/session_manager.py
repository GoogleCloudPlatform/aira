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
Module containing the session manager.
"""

import uuid

from api import errors, models, ports

from . import schemas


class SessionManager:
    """
    Session manager to get user info based on token.
    """

    token_data: schemas.TokenData
    get_session_query: ports.GetSession
    session: models.Session | None

    def __init__(
        self,
        token_data: schemas.TokenData,
        get_session_query: ports.GetSession,
        session: models.Session | None = None,
    ) -> None:
        self.token_data = token_data
        self.get_session_query = get_session_query
        self.session = session

    async def get_current_session(self) -> models.Session:
        """
        Get session from database.
        """
        if not self.session:
            session_id = self.token_data.sub.split(":")[0]
            session_uuid = uuid.UUID(session_id)
            self.session = await self.get_session_query(session_uuid)
            if not self.session:
                raise errors.TokenExpired()
        return self.session
