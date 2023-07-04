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
Module related to all dashboard stuff.
"""
import abc

from starlette import datastructures

from api import models


class Dashboard(abc.ABC):
    """
    The port for the dashboard functions.
    """

    @abc.abstractmethod
    async def get_signed_url(
        self,
        user: models.User,
        query: datastructures.QueryParams,
    ) -> str:
        """
        Generates signed url to access the dashboard.
        """
