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
Module to handle a couple smoke tests.
"""
import contextlib

import pytest

from api.routers.auth import schemas
from tests.helpers import database


@pytest.mark.asyncio
@pytest.mark.disable_autouse
async def test_smoke() -> None:
    """
    Smoke test.
    """
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(database.clear_between_tests())
        role = await stack.enter_async_context(database.role())
        user = await stack.enter_async_context(database.user_with_password(role))
        request = schemas.EmailPasswordLogin(
            email_address=user.email_address,
            password="test",
        )
        test_client = await stack.enter_async_context(database.test_client())
        response = await test_client.post("/api/v1/auth/token", json=request.dict())
        assert response.status_code == 200
