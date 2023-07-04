"""
Module related to the port of the secret manager.
"""
import abc

Secrets = str


# pylint: disable=too-few-public-methods
class SecretManager(abc.ABC):
    """
    Port related to secret managing.
    """

    @abc.abstractmethod
    async def read(self, secret_id: str) -> Secrets | None:
        """
        Read from the secret manager to get the specific secret.
        """
