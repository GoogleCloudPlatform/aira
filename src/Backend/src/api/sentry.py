import logging
import typing

import sentry_sdk
from sentry_sdk.envelope import Envelope
from sentry_sdk.integrations import logging as sentry_logging
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.grpc import GRPCIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from api import typings


class _OfflineTransport(sentry_sdk.Transport):
    def capture_event(self, event: typing.Any) -> None:
        # Assume we originally logged the event as an exception with exc_info=True,
        # so the info should already be logged, no need to do anything here
        pass

    def capture_envelope(self, envelope: Envelope) -> None:
        logging.debug(
            "Sentry envelope",
            extra={"envelope": {"headers": envelope.headers, "items": envelope.items}},
        )


OfflineTransport = _OfflineTransport()


def setup(settings: typings.Settings) -> None:
    transport = None
    dsn = settings.get("sentry_dsn")
    if dsn:
        logging.info("Initialising Sentry with DSN")
    else:
        logging.info("Initialising Sentry with custom transport")
        transport = OfflineTransport

    _sentry_logging = sentry_logging.LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )
    sentry_sdk.init(
        dsn=dsn,
        environment=settings.get("project_id"),
        release=settings.get("git_sha"),
        default_integrations=True,
        auto_enabling_integrations=False,
        integrations=[
            _sentry_logging,
            AioHttpIntegration(),
            AsyncioIntegration(),
            GRPCIntegration(),
            SqlalchemyIntegration(),
        ],
        in_app_include=["api."],
        transport=transport,
    )
