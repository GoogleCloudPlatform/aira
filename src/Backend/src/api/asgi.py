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
Module containing factory to build app.
"""
import functools
import logging

import fastapi
import fastapi_injector
import fastapi_pagination
import injector
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import exceptions
from starlette.middleware.base import BaseHTTPMiddleware

from api import errors, routers, tracing, typings

from . import logging_config
from .middleware import (
    default_error_handler,
    error_handler,
    firebase_handler,
    logging_middleware,
)

logger = logging.getLogger(__name__)


def create_app(container: injector.Injector) -> fastapi.FastAPI:
    """
    Creates fastapi app.
    """
    setts = container.get(typings.Settings)
    if setts.get("env", "prod") != "local":
        container.call_with_injection(
            logging_config.configure, kwargs={"processors": None}
        )

    app = fastapi.FastAPI()
    tracing.setup(app, setts.get("export_to", "google"))

    app.add_middleware(fastapi_injector.InjectorMiddleware, injector=container)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[setts.get("origin")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logging_func = functools.partial(
        logging_middleware, project_id=setts.get("project_id")
    )
    app.add_middleware(BaseHTTPMiddleware, dispatch=logging_func)

    app.include_router(routers.groups_router, prefix="/api/v1/groups")
    app.include_router(routers.organizations_router, prefix="/api/v1/organizations")
    app.include_router(routers.processor_router, prefix="/api/v1/processor")
    app.include_router(routers.base_router, prefix="/api/v1")
    app.include_router(routers.auth_router, prefix="/api/v1/auth")
    app.include_router(routers.users_router, prefix="/api/v1/users")
    app.include_router(routers.roles_router, prefix="/api/v1/roles")
    app.include_router(routers.exams_router, prefix="/api/v1/exams")

    app.add_exception_handler(errors.BaseError, handler=error_handler)
    app.add_exception_handler(exceptions.FirebaseError, handler=firebase_handler)
    app.add_exception_handler(Exception, handler=default_error_handler)

    fastapi_pagination.add_pagination(app)

    fastapi_injector.attach_injector(app, container)

    return app
