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
Module related to the port of any external auth.
"""
import abc
import typing


# pylint: disable=too-few-public-methods
class ExternalAuth(abc.ABC):
    """
    Port related to external auth.
    """

    @abc.abstractmethod
    async def login_from_token(self, token: str) -> dict[str, typing.Any]:
        """
        Login token based.
        """
