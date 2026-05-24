"""
Module containing memory implementation for the secret manager.
"""

import logging
import os
import typing

from api import ports

logger = logging.getLogger(__name__)


class SecretManager(ports.SecretManager):
    """
    memory implementation class for the secret manager.
    """

    Secrets: typing.TypeAlias = ports.Secrets

    def __init__(self) -> None:
        secret = None
        public = None

        # Try to load from files if they exist
        if os.path.exists("tests/private.pem") and os.path.exists("tests/public.pem"):
            try:
                with open("tests/private.pem", encoding="utf-8") as f:
                    secret = f.read()
                with open("tests/public.pem", encoding="utf-8") as f:
                    public = f.read()
                logger.info("Loaded keys from tests/ directory")
            except Exception as e:
                logger.warning(f"Failed to read key files: {e}")

        # If not loaded, generate them in memory
        if not secret or not public:
            logger.info("Generating temporary RSA keys for SecretManager")
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            secret = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")

            public_key = private_key.public_key()
            public = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

        self._secret_data: dict[str, typing.Any] = {
            "public-key": public,
            "private-key": secret,
        }

    async def read(self, secret_id: str) -> Secrets | None:
        return self._secret_data.get(secret_id)
