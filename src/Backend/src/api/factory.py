"""
Module containing factory to build app.
"""

import logging

import fastapi
import fastapi_injector
import fastapi_pagination
import injector
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import exceptions

from api import errors, routers, sentry, tracing, typings

from . import logging_config
from .middleware import (
    LoggingMiddleware,
    default_error_handler,
    error_handler,
    firebase_handler,
    start_middleware,
)

logger = logging.getLogger(__name__)


def create_app(container: injector.Injector) -> fastapi.FastAPI:
    """
    Creates fastapi app.
    """
    setts = container.get(typings.Settings)
    app = fastapi.FastAPI(title="LIA", version="0.5.2")
    tracing_context = container.get(tracing.TracingContext)
    sentry.setup(settings=setts)
    logging_config.configure(
        processors=None,
        level=setts.get("log_level"),
        fmt=setts.get("log_format"),
    )

    app.add_middleware(fastapi_injector.InjectorMiddleware, injector=container)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=setts.get("origin", "").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        LoggingMiddleware,
        log_context=container.get(logging_config.LogContext),
        tracing_context=tracing_context,
        project_id=setts.get("project_id", "unknown"),
    )

    app.include_router(routers.groups_router, prefix="/api/v1/groups")
    app.include_router(routers.organizations_router, prefix="/api/v1/organizations")
    app.include_router(routers.processor_router, prefix="/api/v1/processor")
    app.include_router(routers.base_router, prefix="/api/v1")
    app.include_router(routers.auth_router, prefix="/api/v1/auth")
    app.include_router(routers.users_router, prefix="/api/v1/users")
    app.include_router(routers.roles_router, prefix="/api/v1/roles")
    app.include_router(routers.exams_router, prefix="/api/v1/exams")
    app.include_router(routers.locations_router, prefix="/api/v1/locations")
    app.include_router(routers.series_router, prefix="/api/v1/series")
    app.include_router(routers.shifts_router, prefix="/api/v1/shifts")
    app.include_router(routers.tutorials_router, prefix="/api/v1/tutorials")
    app.include_router(routers.knowledge_base_router, prefix="/api/v1/admin/knowledge-base")


    app.add_exception_handler(
        errors.BaseError,
        handler=error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(exceptions.FirebaseError, handler=firebase_handler)
    app.add_exception_handler(Exception, handler=default_error_handler)

    fastapi_pagination.add_pagination(app)
    # tracing_context.setup(app)

    fastapi_injector.attach_injector(app, container)
    if setts.get("env", "local") == "local":
        start_middleware(app)

    return app


# Trigger reload after .env change (5)
