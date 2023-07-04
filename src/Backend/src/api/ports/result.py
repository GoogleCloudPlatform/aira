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
Module related to the port of result repository.
"""
import abc
import uuid

from api import models


class ResultRepository(abc.ABC):
    """
    Result repository implementation that returns exam data.
    """

    @abc.abstractmethod
    async def get(
        self,
        result_id: uuid.UUID,
    ) -> models.ExamUserQuestion:
        """
        Returns the model data.
        """

    @abc.abstractmethod
    async def create(
        self,
        result_model: models.ExamUserQuestion,
    ) -> models.ExamUserQuestion:
        """
        Creates and return the result model.

        :param result_model: the result model parameter.
        """

    @abc.abstractmethod
    async def delete(self, result_model: models.ExamUserQuestion) -> None:
        """
        Method to delete a result.

        :param result_model: the result model parameter.
        """
