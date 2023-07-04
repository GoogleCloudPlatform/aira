"""
Module containing memory implementation for the secret manager.
"""
import typing

from api import ports


class SecretManager(ports.SecretManager):
    """
    memory implementation class for the secret manager.
    """

    Secrets: typing.TypeAlias = ports.Secrets

    def __init__(self) -> None:
        with open("tests/private.pem", encoding="utf-8") as f:
            secret = f.read()
        with open("tests/public.pem", encoding="utf-8") as f:
            public = f.read()
        self._secret_data: dict[str, typing.Any] = {
            "public-key": public,
            "private-key": secret,
        }

    async def read(self, secret_id: str) -> Secrets | None:
        return self._secret_data.get(secret_id)
