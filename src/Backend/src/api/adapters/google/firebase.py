"""
Module with the implementation of google firebase
"""
import asyncio
import functools
import logging
import typing

import firebase_admin as fb
from firebase_admin import auth

from api import ports

logger = logging.getLogger(__name__)


class FirebaseAuth(ports.ExternalAuth):
    """
    Implementation of google's firebase auth.
    """

    def __init__(self, project_id: str, creds_path: str) -> None:
        credentials = None
        if creds_path:
            credentials = fb.credentials.Certificate(creds_path)
        options = {"projectId": project_id}
        self.client: fb.App = fb.initialize_app(credentials, options=options)
        self.project_id = project_id

    async def login_from_token(self, token: str) -> dict[str, typing.Any]:
        """
        Login token based.
        """
        result: dict[str, typing.Any] = await asyncio.to_thread(
            functools.partial(
                auth.verify_id_token,
                id_token=token,
                app=self.client,
                check_revoked=True,
            )
        )
        return result
