"""
Module that tests all exception handlers.
"""
# pylint: disable=import-private-name
import json
import unittest.mock

import fastapi
import hypothesis
import pytest
from firebase_admin import _token_gen as tkn
from firebase_admin import exceptions
from hypothesis import strategies as st

from api import errors, middleware


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["exception", "status_code"],
    [
        (
            errors.NotFound(),
            fastapi.status.HTTP_404_NOT_FOUND,
        )
    ],
)
async def test_error_handler(exception: errors.BaseError, status_code: int) -> None:
    """
    it tests the error handler for known errors
    """
    request = unittest.mock.Mock()
    response = await middleware.error_handler(request, exception)
    assert response.status_code == status_code
    assert json.loads(response.body) == exception.output


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["exception", "status_code", "message", "code"],
    [
        (
            tkn.ExpiredIdTokenError("", ""),
            fastapi.status.HTTP_400_BAD_REQUEST,
            "The firebase token is expired.",
            "expired_firebase_token",
        )
    ],
)
async def test_firebase_handler(
    exception: exceptions.FirebaseError, status_code: int, message: str, code: str
) -> None:
    """
    it tests the error handler for known errors
    """
    request = unittest.mock.Mock()
    response = await middleware.firebase_handler(request, exception)
    assert response.status_code == status_code
    output = {
        "status_code": status_code,
        "code": code,
        "message": message,
    }
    assert json.loads(response.body) == output


@pytest.mark.asyncio
@hypothesis.given(exception=st.builds(Exception))
async def test_default_error_handler(
    exception: Exception,
) -> None:
    """
    it tests the error handler for known errors
    """
    request = unittest.mock.Mock()
    response = await middleware.default_error_handler(request, exception)
    assert response.status_code == 500
    output = {
        "status_code": 500,
        "code": "unexpected_server_error",
        "message": "There was an unexpected server error.",
    }
    assert json.loads(response.body) == output
