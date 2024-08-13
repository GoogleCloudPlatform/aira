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
