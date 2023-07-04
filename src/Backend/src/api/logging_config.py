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
Helper functions to setup structured logging.
"""
from __future__ import annotations

import logging
import logging.config
import typing

import injector
import structlog

from api.typings import Settings


def gcp_source_location(
    logger: logging.Logger | None,  # pylint: disable=unused-argument
    name: str,  # pylint: disable=unused-argument
    event_dict: structlog.typing.EventDict,
) -> structlog.typing.EventDict:
    """
    GCP Source Location.

    add the location of the logging statement in the code to GCP logs

    see:
    https://cloud.google.com/logging/docs/agent/logging/configuration#special-fields
    """
    record: logging.LogRecord | None = event_dict.get("_record")

    if record:
        event_dict = event_dict | {
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }
        }

    return event_dict


shared_processors: tuple[structlog.types.Processor, ...] = (
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.format_exc_info,
    gcp_source_location,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.ExtraAdder(),
)


def get_logging_config(
    log_level: str,
    log_format: str,
    processors: tuple[structlog.types.Processor, ...] | None = None,
) -> dict[str, typing.Any]:
    """
    Generate dictionary with configuration for structlog.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": processors or shared_processors,
            },
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
                "foreign_pre_chain": processors or shared_processors,
            },
        },
        "handlers": {
            "default": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": log_format,
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": log_level,
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


@injector.inject
def configure(
    settings: Settings, processors: tuple[structlog.types.Processor, ...] | None = None
) -> None:
    """
    Configure logging based on settings.
    """
    logging.config.dictConfig(
        get_logging_config(
            processors=processors,
            log_level=settings.get("log_level", "INFO"),
            log_format=settings.get("log_format", "json"),
        )
    )
