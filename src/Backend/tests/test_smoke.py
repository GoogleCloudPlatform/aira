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
