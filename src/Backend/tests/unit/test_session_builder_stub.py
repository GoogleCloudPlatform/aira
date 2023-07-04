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
Unit test for session memory implementation.
"""

import pytest

from api.adapters.memory import unit_of_work


@pytest.mark.asyncio
async def test_it_should_create_session() -> None:
    """
    it should create session memory implementation
    """
    uow_builder = unit_of_work.UnitOfWorkBuilder()
    async with uow_builder() as uow:
        assert uow.closed is False
        assert isinstance(uow, unit_of_work.UnitOfWork)
    assert uow.closed is True
