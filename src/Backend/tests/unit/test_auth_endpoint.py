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
Unit tests for `process`
"""
import unittest.mock

import hypothesis
import pytest
from hypothesis import strategies as st
from passlib import context

from api import typings
from api.adapters.memory import external_auth, secret_manager, unit_of_work
from api.routers.auth import endpoints as auth_endpoint
from api.routers.auth import schemas


@pytest.mark.asyncio
@hypothesis.given(
    request=st.builds(
        schemas.FirebaseLogin,
    ),
    response=st.builds(schemas.Session),
)
@hypothesis.settings(
    max_examples=8,
    suppress_health_check=[hypothesis.HealthCheck.function_scoped_fixture],
)
async def test_login_calls_properly(
    request: schemas.FirebaseLogin,
    response: schemas.Session,
    hash_ctx: context.CryptContext,
) -> None:
    """
    tests if auth endpoint calls correctly.
    """
    login_mock = unittest.mock.AsyncMock()
    login_mock.return_value = response
    uow_builder = unit_of_work.UnitOfWorkBuilder(user_repository=None)
    with unittest.mock.patch("api.routers.auth.crud.login", login_mock):
        response = await auth_endpoint.login(
            external_login=external_auth.ExternalAuth(),
            secret_manager=secret_manager.SecretManager(),
            settings=typings.Settings({}),
            uow_builder=uow_builder,
            body=request,
            hash_ctx=hash_ctx,
        )
    login_mock.assert_awaited_once()
    assert uow_builder.call_count == 1
    assert response.json() == response.json()
