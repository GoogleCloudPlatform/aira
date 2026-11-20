import logging
import typing

import sentry_sdk
from sentry_sdk.envelope import Envelope
from sentry_sdk.integrations import logging as sentry_logging
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.grpc import GRPCIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from api import logging_config, typings


def _scrub_sentry_event(
    event: typing.Any,
    hint: typing.Any,
) -> typing.Any:
    del hint
    return logging_config.redact_value(event)


def _scrub_sentry_breadcrumb(
    crumb: dict[str, typing.Any],
    hint: typing.Any,
) -> dict[str, typing.Any]:
    del hint
    return typing.cast(dict[str, typing.Any], logging_config.redact_value(crumb))


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
        send_default_pii=False,
        include_local_variables=False,
        before_send=_scrub_sentry_event,
        before_breadcrumb=_scrub_sentry_breadcrumb,
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
