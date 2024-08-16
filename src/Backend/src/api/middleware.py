"""
Middleware file for the connector runtime.
"""

# pylint: disable=import-private-name
import collections.abc
import json
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

from api import errors, logging_config, tracing

NextCall = collections.abc.Callable[
    [fastapi.Request], collections.abc.Awaitable[starlette.responses.Response]
]

logger = logging.getLogger(__name__)


class LoggingMiddleware(starlette.middleware.base.BaseHTTPMiddleware):
    """
    Logging middleware for google cloud logging.

    Logs the request and response.
    """

    def __init__(
        self,
        app: starlette.types.ASGIApp,
        log_context: logging_config.LogContext,
        tracing_context: tracing.TracingContext,
        project_id: str,
    ) -> None:
        self.project_id = project_id
        self.log_context = log_context
        self.tracing_context = tracing_context
        super().__init__(app)

    def _get_trace(self, request: starlette.requests.Request) -> str | None:
        """
        Get trace path from request.

        Build the trace path from the request. The trace identifier is extracted from
        the TraceParent header, and then combined with the project identifier to form
        the trace path.

        Header Example: `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`

        Documentation on the header format can be found here:

        https://www.w3.org/TR/trace-context/#traceparent-header-field-values

        :param request: request object

        :returns: trace id or None if not found
        """
        if (value := request.headers.get("traceparent")) and value[:3] == "00-":
            trace_id = value.split("-")[1]

            return f"projects/{self.project_id}/traces/{trace_id}"

        return None

    def _build_http_request(
        self, request: starlette.requests.Request
    ) -> dict[str, str | int | None]:
        """
        Build a http request object.

        Build the google cloud logging HTTP request object from the request.

        This can be used to provide additional structured information in the google
        cloud logging viewer, making it consistent with logs added by parts of the
        google cloud infrastructure.

        This only populates the request related fields.

        Documentation on the HTTP request object can be found here:

        https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#HttpRequest

        :param request: request object

        :returns: request object
        """
        result = {
            "requestMethod": request.method,
            "requestUrl": str(request.url),
            "requestSize": request.headers.get("content-length"),
            "userAgent": request.headers.get("user-agent"),
            "remoteIp": request.client.host if request.client else None,
            "serverIp": request["server"][0] if "server" in request else None,
            "referer": request.headers.get("referer"),
            "protocol": f"HTTP/{request['http_version']}",
        }

        return {k: v for k, v in result.items() if v is not None}

    async def _build_http_info(
        self,
        request: starlette.requests.Request,
        response: starlette.responses.Response,
        latency: float,
    ) -> dict[str, typing.Any]:
        if isinstance(response, starlette.responses.StreamingResponse):
            chunks = [section async for section in response.body_iterator]

            response.body_iterator = starlette.concurrency.iterate_in_threadpool(
                iter(chunks)
            )

            body = b"".join(
                (chunk.encode("utf-8") if isinstance(chunk, str) else chunk)
                for chunk in chunks
            )
        else:
            body = response.body

        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = None

        return dict(
            method=request.method,
            url=str(request.url),
            status=response.status_code,
            body=body,
            data=data,
            headers=dict(response.headers),
            latency=latency,
        )

    async def _get_route(self, request: starlette.requests.Request) -> str | None:
        """
        Get route from request.

        Retrieve the route from the request. The route is extracted from the scope.

        :param request: request object

        :returns: route or None if not found
        """
        route = request.scope.get("route")

        route_classes = (
            starlette.routing.Route,
            starlette.routing.WebSocketRoute,
            starlette.routing.Mount,
        )

        if isinstance(route, route_classes):
            return route.path

        return None

    async def dispatch(
        self,
        request: starlette.requests.Request,
        call_next: starlette.middleware.base.RequestResponseEndpoint,
    ) -> starlette.responses.Response:
        """
        Dispatch.

        Intercept and log the request, call the next middleware and then log the
        response along with the latency.

        :param request: request object
        :param call_next: the next call in the middleware chain

        :returns: response from call_next
        """
        start_time = time.perf_counter()
        self.tracing_context.load_baggage()

        with (
            self.log_context.add("httpRequest", self._build_http_request(request)),
            self.log_context.add(
                "logging.googleapis.com/trace", self._get_trace(request)
            ),
            self.log_context.add(
                "tracing", self.tracing_context.tracing_extras_for_logging()
            ),
        ):
            response = await call_next(request)

            latency = time.perf_counter() - start_time

            http_info = await self._build_http_info(request, response, latency)

            with (
                self.log_context.update(
                    "httpRequest",
                    {
                        "status": str(response.status_code),
                        "responseSize": response.headers.get(
                            "content-length",
                            len(http_info["body"]) if http_info.get("body") else 0,
                        ),
                        "latency": str(latency),
                    },
                ),
                self.log_context.add("route", await self._get_route(request)),
            ):
                logger.info(
                    "response",
                    extra={"http_info": http_info},
                )

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
