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
Module for all result related sqlalchemy memory implementation queries.
"""
import uuid

from api import errors, models, ports
from api.helpers import time_now


class ResultRepository(ports.ResultRepository):
    """
    Result repository memory implementation that returns result data.
    """

    def __init__(self, items: list[models.ExamUserQuestion] | None = None) -> None:
        self._items = items if items else []

    async def get(
        self,
        result_id: uuid.UUID,
    ) -> models.ExamUserQuestion:
        """
        Get result by params.

        :params result_id: result id on database.
        """
        if self._items:
            items = self._items
            items = [item for item in items if item.id == result_id]
            if len(items) == 1:
                return items[0]
        raise errors.NotFound

    async def create(
        self, result_model: models.ExamUserQuestion
    ) -> models.ExamUserQuestion:
        """
        Method to create a result for the user.

        :param result_model: the result model parameter.

        :returns: result model.
        """
        if any(item for item in self._items if item.id == result_model.id):
            raise errors.AlreadyExists()
        result_model.created_at = result_model.updated_at = time_now()
        self._items.append(result_model)
        return result_model

    async def delete(self, result_model: models.ExamUserQuestion) -> None:
        """
        Method to delete a result.

        :param result_model: the result model parameter.
        """
        self._items = [item for item in self._items if item.id != result_model.id]
