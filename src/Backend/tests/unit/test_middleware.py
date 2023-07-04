"""
Unit tests for middleware
"""

import logging
import unittest.mock
import uuid

import fastapi
import pytest
import starlette

from api import middleware


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [200, 400, 500])
async def test_custom_middleware_log(
    status_code: int,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    it should log properly the data from request and response
    """
    content_type = "application/json"
    content = b'{"a": "b"}'

    caplog.clear()
    caplog.set_level(logging.INFO)
    # pylint: disable=use-dict-literal
    request = fastapi.Request(
        scope=dict(
            type="http",
            method="POST",
            path="/test",
            headers={},
            route=starlette.routing.Route(path="/test", endpoint=unittest.mock.Mock()),
            root_path="",
        )
    )
    call_next_mock = unittest.mock.AsyncMock()
    call_next_mock.return_value = fastapi.Response(
        content=content, media_type=content_type, status_code=status_code
    )
    trace_id = str(uuid.uuid4())
    with unittest.mock.patch("api.tracing.get_trace_data") as trace_mock:
        trace_mock.return_value = {"trace_id": trace_id}
        await middleware.logging_middleware(request=request, call_next=call_next_mock)

    expected_http_request = {
        "requestMethod": "POST",
        "requestUrl": unittest.mock.ANY,
        "requestSize": None,
        "status": status_code,
        "responseSize": "10",
        "userAgent": None,
        "remoteIp": None,
        "latency": unittest.mock.ANY,
    }
    assert len(caplog.records) == 1
    if status_code >= 500:
        assert caplog.records[0].levelname == "ERROR"
    elif status_code >= 400:
        assert caplog.records[0].levelname == "WARNING"
    else:
        assert caplog.records[0].levelname == "INFO"
    assert (
        caplog.records[0].httpRequest  # type: ignore[attr-defined]
        == expected_http_request
    )
