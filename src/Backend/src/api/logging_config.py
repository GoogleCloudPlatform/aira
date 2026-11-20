"""
Logging related helpers and utilities.
"""

import abc
import collections.abc
import contextlib
import logging.config
import re
import typing

import structlog.contextvars

T = typing.TypeVar("T")

REDACTED = "[REDACTED]"
_MAX_REDACT_DEPTH = 20
_STRUCTLOG_INTERNAL_KEYS: frozenset[str] = frozenset({"_record", "_from_structlog"})

_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "_password",
        "passwd",
        "pwd",
        "secret",
        "client_secret",
        "looker_secret",
        "private_key",
        "api_key",
        "apikey",
        "x_api_key",
        "sendgrid_key",
        "smtp_password",
        "token",
        "id_token",
        "access_token",
        "refresh_token",
        "reset_token",
        "seduc_token",
        "authorization",
        "cookie",
        "set_cookie",
        "email",
        "email_address",
    }
)

_SENSITIVE_KEY_PATTERN = (
    r"(?:_?password|passwd|pwd|client_secret|looker_secret|private_key|"
    r"api_key|apikey|x-api-key|sendgrid_key|smtp_password|"
    r"id_token|access_token|refresh_token|reset_token|seduc_token|"
    r"authorization|cookie|set-cookie|email_address|email|secret|token)"
)

_QUERY_SECRET_RE = re.compile(
    r"([?&](?:_?password|passwd|secret|token|id_token|access_token|"
    r"refresh_token|reset_token|api_key|apikey|sig|signature)=)"
    r"[^&\s'\"<>]+",
    re.IGNORECASE,
)

_BEARER_RE = re.compile(r"\b(Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE)

_QUOTED_KV_SECRET_RE = re.compile(
    rf"""(?P<prefix>(?P<kquote>['"]){_SENSITIVE_KEY_PATTERN}(?P=kquote)\s*:\s*)"""
    rf"""(?P<value>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^\s,}}\]]+)""",
    re.IGNORECASE,
)

_UNQUOTED_KV_SECRET_RE = re.compile(
    rf"""(?P<prefix>(?<![A-Za-z0-9_]){_SENSITIVE_KEY_PATTERN}\s*[:=]\s*)"""
    rf"""(?P<value>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|[^\s,}}\]&;]+)""",
    re.IGNORECASE,
)


def _is_sensitive_key(key: typing.Any) -> bool:
    if not isinstance(key, str):
        return False
    return key.strip().lower().replace("-", "_") in _SENSITIVE_KEYS


def _replace_kv_match(match: re.Match[str]) -> str:
    prefix = match.group("prefix")
    value = match.group("value")
    if value.startswith('"'):
        return f'{prefix}"{REDACTED}"'
    if value.startswith("'"):
        return f"{prefix}'{REDACTED}'"
    return f"{prefix}{REDACTED}"


def redact_string(value: str) -> str:
    """Scrub plaintext credentials, tokens, and PII key-value pairs from a string."""
    scrubbed = _QUERY_SECRET_RE.sub(rf"\1{REDACTED}", value)
    scrubbed = _BEARER_RE.sub(rf"\1{REDACTED}", scrubbed)
    scrubbed = _QUOTED_KV_SECRET_RE.sub(_replace_kv_match, scrubbed)
    scrubbed = _UNQUOTED_KV_SECRET_RE.sub(_replace_kv_match, scrubbed)
    return scrubbed


def redact_value(
    value: typing.Any,
    *,
    _depth: int = 0,
    preserve_internal_keys: bool = False,
) -> typing.Any:
    """Recursively scrub sensitive keys and secret patterns from structured data."""
    if _depth >= _MAX_REDACT_DEPTH:
        return REDACTED
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, collections.abc.Mapping):
        redacted_map: dict[typing.Any, typing.Any] = {}
        for k, v in value.items():
            if preserve_internal_keys and k in _STRUCTLOG_INTERNAL_KEYS:
                redacted_map[k] = v
            elif _is_sensitive_key(k):
                redacted_map[k] = REDACTED
            else:
                redacted_map[k] = redact_value(v, _depth=_depth + 1)
        return redacted_map
    if isinstance(value, list):
        return [redact_value(item, _depth=_depth + 1) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item, _depth=_depth + 1) for item in value)
    return value


def redact_sensitive_data(
    logger: logging.Logger | None,
    name: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    """Structlog processor that redacts credentials and PII before rendering logs."""
    return typing.cast(
        structlog.typing.EventDict,
        redact_value(event_dict, preserve_internal_keys=True),
    )


class LogContext(metaclass=abc.ABCMeta):
    """
    Log context.
    """

    def __merge(self, current: typing.Any, other: T) -> T:
        """
        Merge current and other values.
        """
        if isinstance(current, dict) and isinstance(other, dict):
            return typing.cast(T, current | other)

        return other

    @abc.abstractmethod
    def get(self, key: str) -> typing.Any:
        """
        Get value from logging context.

        Get the value of key in the logging context. If the value does not exist,
        None will be returned.

        :param key: The key to get.

        :return: The value of key in the logging context or None if no value exists.
        """

    @abc.abstractmethod
    def add(
        self, key: str, value: typing.Any
    ) -> contextlib.AbstractContextManager[None]:
        """
        Add value to logging context.

        Add or replace the value of key in the logging context.

        :param key: The key to update.
        :param value: The value to update.

        :return: A context manager that will remove the value from the logging context
                 when exited.
        """

    def update(
        self, key: str, value: typing.Any
    ) -> contextlib.AbstractContextManager[None]:
        """
        Update value in logging context.

        Add or update the value of key in the logging context. If the value is a
        dictionary, and the current value is a dictionary, the values will be merged.

        :param key: The key to update.
        :param value: The value to update.

        :return: A context manager that will remove the value from the logging context
                 when exited.
        """
        return self.add(key, self.__merge(self.get(key), value))


class StructLogLogContext(LogContext):
    """
    StructLog logging context.
    """

    @contextlib.contextmanager
    def add(self, key: str, value: typing.Any) -> collections.abc.Iterator[None]:
        with structlog.contextvars.bound_contextvars(**{key: value}):
            yield

    def get(self, key: str) -> typing.Any:
        return structlog.contextvars.get_contextvars().get(key)


def add_gcp_severity(
    logger: logging.Logger | None,
    name: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    """
    GCP Severity.

    Add the severity of the logging statement to GCP logs.

    See: https://cloud.google.com/logging/docs/structured-logging
    """
    level = event_dict.get("level")  # requires `structlog.stdlib.add_log_level`
    if level:
        event_dict["severity"] = level.upper()

    return event_dict


def gcp_source_location(
    logger: logging.Logger | None,
    name: str,
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    """
    GCP Source Location.

    add the location of the logging statement in the code to GCP logs

    see:
    https://cloud.google.com/logging/docs/agent/logging/configuration#special-fields
    """
    record = event_dict.get("_record")

    if isinstance(record, logging.LogRecord):
        event_dict = {
            **event_dict,
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
        }

    return event_dict


default_processors: tuple[structlog.types.Processor, ...] = (
    structlog.contextvars.merge_contextvars,
    # Add the name of the logger to event dictionary
    structlog.stdlib.add_logger_name,
    # Add log level to event dictionary
    structlog.stdlib.add_log_level,
    # Add GCP severity to event dictionary
    add_gcp_severity,
    # If the "exc_info" key in the event dictionary is either true or a
    # sys.exc_info() tuple, remove "exc_info" and render the exception
    # with traceback into the "exception" key.
    structlog.processors.format_exc_info,
    gcp_source_location,
    # Add a timestamp in ISO 8601 format
    structlog.processors.TimeStamper(fmt="iso"),
    # Add extra attributes of LogRecord objects to the event dictionary
    # so that values passed in the extra parameter of log methods pass
    # through to log output.
    structlog.stdlib.ExtraAdder(),
    # Scrub credentials, tokens, and PII before rendering to Cloud Logging.
    redact_sensitive_data,
)

LOG_RENDERER = {
    "json": structlog.processors.JSONRenderer,
    "console": structlog.dev.ConsoleRenderer,
}


def get_logging_config(
    level: str,
    fmt: str,
    processors: collections.abc.Iterable[structlog.types.Processor] | None = None,
) -> dict[str, typing.Any]:
    """
    Generate dictionary with configuration for structlog.
    """
    # Configuration based on
    # https://www.structlog.org/en/stable/standard-library.html
    # #rendering-using-structlog-based-formatters-within-logging

    if not processors:
        processors = default_processors

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": LOG_RENDERER[fmt](),
                "foreign_pre_chain": list(processors),
            },
        },
        "handlers": {
            "default": {
                "level": level,
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": level,
            },
            "uvicorn.error": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine.Engine": {
                "handlers": ["default"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }


def configure(
    level: str | None,
    fmt: str | None,
    processors: collections.abc.Iterable[structlog.types.Processor] | None = None,
) -> None:
    """
    Configure logging based on settings.
    """
    logging.config.dictConfig(
        get_logging_config(
            processors=processors,
            level=level or "INFO",
            fmt=fmt or "json",
        )
    )
