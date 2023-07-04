"""
Tracing setup file.
"""

import logging
import random
import typing

import fastapi
from opentelemetry import baggage, trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context import attach
from opentelemetry.context.context import Context
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation import requests
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.grpc import (
    GrpcAioInstrumentorClient,
    GrpcInstrumentorClient,
)
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators import cloud_trace_propagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.resourcedetector import gcp_resource_detector
from opentelemetry.sdk import resources
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider, export


def client_response_hook(span: trace.Span, message: dict[str, typing.Any]) -> None:
    """
    Response hook to execute custom logic to be performed after performing a request.

    The client response hook is called with the internal span and an ASGI event which is
    sent as a dictionary for when the method send is called.
    """
    try:
        if message["type"] == "http.response.body":
            if span and span.is_recording():
                span.set_attribute(
                    "http.response.body", message["body"].decode("utf-8")
                )
    except (KeyError, UnicodeError) as exception:
        logging.exception(exception)


def setup(app: fastapi.FastAPI, export_to: str) -> trace.Tracer | None:
    """
    Setting tracing up.
    """
    tracer_provider_kwargs = {}
    trace_exporter: SpanProcessor

    match export_to:
        case "google":
            resource = resources.get_aggregated_resources(
                [
                    gcp_resource_detector.GoogleCloudResourceDetector(
                        raise_on_error=True
                    )  # type: ignore[no-untyped-call]
                ]
            )
            tracer_provider_kwargs = {"resource": resource}
            trace_exporter = export.BatchSpanProcessor(
                CloudTraceSpanExporter()  # type: ignore[no-untyped-call]
            )
        case "console":
            trace_exporter = (  # pylint: disable=redefined-variable-type
                export.SimpleSpanProcessor(export.ConsoleSpanExporter())
            )
        case _:
            return None

    set_global_textmap(
        CompositePropagator(
            [
                cloud_trace_propagator.CloudTraceFormatPropagator(),
                W3CBaggagePropagator(),
            ]
        )
    )

    tracer_provider = TracerProvider(**tracer_provider_kwargs)  # type: ignore[arg-type]
    tracer_provider.add_span_processor(trace_exporter)
    trace.set_tracer_provider(tracer_provider)

    app.add_event_handler("shutdown", tracer_provider.force_flush)

    FastAPIInstrumentor.instrument_app(app, client_response_hook=client_response_hook)
    AioHttpClientInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    AsyncPGInstrumentor().instrument()  # type: ignore[no-untyped-call]
    SQLAlchemyInstrumentor().instrument()
    GrpcInstrumentorClient().instrument()  # type: ignore[no-untyped-call]
    GrpcAioInstrumentorClient().instrument()  # type: ignore[no-untyped-call]
    requests.RequestsInstrumentor().instrument()

    tracer = trace.get_tracer(__name__)
    return tracer


def get_trace_data(ctx: Context | None = None) -> dict[str, str | None]:
    """
    Get the trace id from the current context.
    """
    span_context = trace.get_current_span(context=ctx).get_span_context()

    trace_data = baggage.get_baggage("trace_id", context=ctx)

    trace_id = str(trace_data) if trace_data else None

    if not trace_id:
        if span_context.is_valid:
            trace_id = trace.format_trace_id(span_context.trace_id)
        else:
            trace_id = trace.format_trace_id(random.getrandbits(128))
    set_tracing_data(trace_id)
    attach(baggage.set_baggage("trace_id", trace_id))
    return {"trace_id": trace_id}


def set_tracing_data(trace_id: str, ctx: Context | None = None) -> None:
    """
    Re set trace data to otel context.
    """
    current_span = trace.get_current_span(context=ctx)
    if current_span.get_span_context().is_valid:
        current_span.set_attribute("trace_id", trace_id)
