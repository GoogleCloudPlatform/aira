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
Module to test container/asgi setup.
"""


import fastapi_injector
import injector
from starlette.middleware import base

from api import asgi, dependencies, middleware


def test_setup_container() -> None:
    """
    it should setup the container.
    """

    container = injector.Injector(dependencies.SettingsModule())

    app = asgi.create_app(container)

    assert app.state.injector is container


def test_setup_injector_middleware() -> None:
    """
    it should setup injector middleware.
    """

    container = injector.Injector(dependencies.SettingsModule())

    app = asgi.create_app(container)

    assert any(
        v.cls == fastapi_injector.InjectorMiddleware for v in app.user_middleware
    )


def test_setup_logging_middleware() -> None:
    """
    it should setup logging middleware
    """

    container = injector.Injector(dependencies.SettingsModule())

    app = asgi.create_app(container)

    # pylint: disable=comparison-with-callable
    assert any(
        v.cls == base.BaseHTTPMiddleware
        and v.options.get("dispatch").func  # type: ignore[union-attr]
        == middleware.logging_middleware
        for v in app.user_middleware
    )
