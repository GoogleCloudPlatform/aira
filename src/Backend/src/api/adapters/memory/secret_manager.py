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
