"""
Module to test container/asgi setup.
"""

import fastapi_injector
import injector
from api import dependencies, factory, middleware


def test_setup_container() -> None:
    """
    it should setup the container.
    """

    container = injector.Injector(
        (
            dependencies.SettingsModule(),
            dependencies.TracingModule(),
        )
    )

    app = factory.create_app(container)

    assert app.state.injector is container


def test_setup_injector_middleware() -> None:
    """
    it should setup injector middleware.
    """

    container = injector.Injector(
        (
            dependencies.SettingsModule(),
            dependencies.TracingModule(),
        )
    )

    app = factory.create_app(container)

    assert any(
        v.cls is fastapi_injector.InjectorMiddleware for v in app.user_middleware
    )


def test_setup_logging_middleware() -> None:
    """
    it should setup logging middleware
    """

    container = injector.Injector(
        (
            dependencies.SettingsModule(),
            dependencies.TracingModule(),
        )
    )

    app = factory.create_app(container)

    assert any(v.cls is middleware.LoggingMiddleware for v in app.user_middleware)
