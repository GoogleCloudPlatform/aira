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
Middleware file for the connector runtime.
"""
# pylint: disable=import-private-name
import collections.abc
import logging
import time
import typing

import fastapi
import pydantic
import starlette.responses
from firebase_admin import _auth_utils as au
from firebase_admin import _token_gen as tkn
from firebase_admin import exceptions
from opentelemetry import trace

from api import errors, tracing

NextCall = collections.abc.Callable[
    [fastapi.Request], collections.abc.Awaitable[starlette.responses.Response]
]

logger = logging.getLogger(__name__)


# pylint: disable=unused-argument
async def logging_middleware(
    request: fastapi.Request,
    call_next: NextCall,
    project_id: str | None = None,
) -> fastapi.Response:
    """
    Log data from request and response.

    Intercepts the request and starts a timer,
    calls back the endpoint and then logs the request,
    response and latency.

    :returns: the response back to the app.
    """
    start_time = time.perf_counter()

    try:
        response: starlette.responses.Response = await call_next(request)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        response = await handle_handlers(request, exc)

    process_time = time.perf_counter() - start_time
    request_url = request.url.path

    http_request = {
        "requestMethod": request.method,
        "requestUrl": request_url,
        "requestSize": request.headers.get("content-length"),
        "status": response.status_code,
        "responseSize": response.headers.get("content-length"),
        "userAgent": request.headers.get("user-agent"),
        "remoteIp": request.client.host if request.client else None,
        "latency": process_time,
    }
    extra = {}

    if response.status_code >= 500:
        level = logging.ERROR
    elif response.status_code >= 400:
        level = logging.WARNING
    else:
        level = logging.INFO

    if request.method.lower() != "options":
        trace_id: str | None = None
        if x_cloud_trace_context_header := request.headers.get("x-cloud-trace-context"):
            trace_id = x_cloud_trace_context_header.partition("/")[0]
            tracing.set_tracing_data(trace_id=trace_id)
        trace_data = tracing.get_trace_data()
        extra = {
            "httpRequest": http_request,
            "tracing": trace_data,
        }
        trace_id = str(trace_data["trace_id"]) if trace_data["trace_id"] else trace_id
        if project_id and isinstance(trace_id, str):
            extra[
                "logging.googleapis.com/trace"
            ] = f"projects/{project_id}/traces/{trace_id}"
        logger.log(level, "response", extra=extra)
    return response


async def error_handler(
    request: fastapi.Request, exc: errors.BaseError
) -> fastapi.responses.Response:
    """
    Error handler for custom errors.
    """
    return fastapi.responses.JSONResponse(
        status_code=exc.output.get("status_code", 400), content=exc.output
    )


async def firebase_handler(
    request: fastapi.Request, exc: exceptions.FirebaseError
) -> fastapi.responses.Response:
    """
    Handler for firebase expected errors.
    """
    match exc:
        case tkn.ExpiredIdTokenError():
            content = {
                "status_code": 400,
                "code": "expired_firebase_token",
                "message": "The firebase token is expired.",
            }
            return fastapi.responses.JSONResponse(
                status_code=fastapi.status.HTTP_400_BAD_REQUEST,
                content=content,
            )
        case au.InvalidIdTokenError():
            content = {
                "status_code": 404,
                "code": "user_not_found",
                "message": "The firebase token doesn't match with an user.",
            }
            return fastapi.responses.JSONResponse(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                content=content,
            )
        case _:
            return await default_error_handler(request, exc)


async def default_error_handler(
    request: fastapi.Request, exc: Exception
) -> fastapi.responses.Response:
    """
    Handler for unexpected errors.
    """
    resp: list[dict[str, typing.Any]] | dict[str, typing.Any] | None = None
    match exc:
        case pydantic.ValidationError():
            status_code = fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY
            resp = [dict(error) for error in exc.errors()]
        case _:
            logger.exception(exc)
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                current_span.record_exception(exc)
            status_code = fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR
            resp = {
                "status_code": 500,
                "code": "unexpected_server_error",
                "message": "There was an unexpected server error.",
            }

    return fastapi.responses.JSONResponse(
        status_code=status_code,
        content=resp,
    )


async def handle_handlers(
    request: fastapi.Request, exc: Exception
) -> fastapi.responses.Response:
    """
    Function to handle the different error handlers.
    """
    match exc:
        case errors.BaseError():
            return await error_handler(request, exc)
        case exceptions.FirebaseError():
            return await firebase_handler(request, exc)
        case _:
            return await default_error_handler(request, exc)
