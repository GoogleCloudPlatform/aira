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
