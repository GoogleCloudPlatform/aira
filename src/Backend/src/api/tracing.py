"""
Tracing setup file.
"""

import abc
import collections.abc
import logging
import random
import typing
from contextvars import ContextVar

from fastapi import FastAPI
from opentelemetry import baggage, propagate, trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context import attach
from opentelemetry.context.context import Context
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.grpc import (
    GrpcAioInstrumentorClient,
    GrpcInstrumentorClient,
)
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.propagators.cloud_trace_propagator import CloudTraceFormatPropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.resourcedetector.gcp_resource_detector import (
    GoogleCloudResourceDetector,
)
from opentelemetry.sdk import resources
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    in_memory_span_exporter,
)

# based on https://blog.arkency.com/correlation-id-and-causation-id-in-evented-systems/
CAUSATION_REQ_ID_BAGGAGE_KEY = "causation_request_id"
TRACE_ID_BAGGAGE_KEY = "trace_id"
_tracing_log_extras_var: ContextVar[dict[str, str | None]] = ContextVar(
    "tracing_log_extras_var"
)
_request_id_var: ContextVar[str] = ContextVar("request_id")


def get_initial_resource(project_id: str, environment: str) -> resources.Resource:
    """
    Return a basic OpenTelemetry Resource identifying the current process.
    """
    return resources.Resource.create(
        {
            "project_id": project_id,
            "environment": environment,
            "service": "stt-exams",
        }
    )


class TracingContext(abc.ABC):
    """
    Tracing context.
    """

    def __init__(self, project_id: str, environment: str) -> None:
        self._project_id = project_id
        self._environment = environment

    @abc.abstractmethod
    def get_trace_processor(self) -> SpanProcessor:
        """
        Get the span processor.
        """

    def get_resources(self) -> resources.Resource:
        """
        Get implementation-specific tracing resources.
        """
        return resources.Resource.create({})

    @classmethod
    def client_response_hook(
        cls, span: trace.Span, message: dict[str, typing.Any]
    ) -> None:
        """
        Response hook to execute custom logic after performing a request.

        The client response hook is called with the internal span and an ASGI event
        which is sent as a dictionary for when the method send is called.
        """
        try:
            if message["type"] == "http.response.body" and span and span.is_recording():
                span.set_attribute(
                    "http.response.body", message["body"].decode("utf-8")
                )
        except (KeyError, UnicodeError) as exception:
            logging.exception(exception)

    def setup(self, app: FastAPI) -> None:
        """
        Set up the tracer.
        """
        initial_resource = get_initial_resource(
            project_id=self._project_id,
            environment=self._environment,
        )
        ctx_resources = self.get_resources()

        trace_processor = self.get_trace_processor()

        # Setup tracing
        tracer_provider = TracerProvider(resource=ctx_resources.merge(initial_resource))
        tracer_provider.add_span_processor(trace_processor)
        trace.set_tracer_provider(tracer_provider)

        # Setup distributed tracing
        propagate.set_global_textmap(
            CompositePropagator([CloudTraceFormatPropagator(), W3CBaggagePropagator()])
        )

        app.add_event_handler("shutdown", tracer_provider.force_flush)
        FastAPIInstrumentor.instrument_app(
            app, client_response_hook=self.client_response_hook
        )
        AioHttpClientInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        AsyncPGInstrumentor().instrument()  # type: ignore[no-untyped-call]
        SQLAlchemyInstrumentor().instrument()
        GrpcInstrumentorClient().instrument()  # type: ignore[no-untyped-call]
        GrpcAioInstrumentorClient().instrument()  # type: ignore[no-untyped-call]

    def _get_current_request_id(self) -> str:
        """
        Get the current request ID.
        """
        try:
            request_id = _request_id_var.get()
        except LookupError:
            request_id = trace.format_trace_id(random.getrandbits(128))
            _request_id_var.set(request_id)
        return request_id

    def get_trace_id(self) -> str:
        """
        Get the trace ID for the current context.
        """
        # get the trace id from the current context, not the propagated one
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:
            # should always get here, as we expect to use this while in a span
            trace_id = trace.format_trace_id(span_context.trace_id)
        else:
            trace_id = self._get_current_request_id()
        return trace_id

    def _set_current_tracing_values(
        self, *, request_id: str, trace_id: str, causation_request_id: str
    ) -> None:
        """
        Store all the tracing values in the current context.
        """
        # set values for logs
        try:
            stored_values = _tracing_log_extras_var.get()
        except LookupError:
            stored_values = {}
            _tracing_log_extras_var.set(stored_values)

        # update in-place to always keep the same dictionary reference
        stored_values.update(
            {
                "request_id": request_id,
                "trace_id": trace_id,
                "causation_request_id": causation_request_id,
            }
        )

        # inject to the current tracing context
        current_span = trace.get_current_span()
        if current_span.get_span_context().is_valid:
            current_span.set_attribute("request_id", request_id)
            current_span.set_attribute("trace_id", trace_id)
            current_span.set_attribute("causation_request_id", causation_request_id)
        else:
            logging.debug("Cannot set tracing baggage attributes on invalid span")

    def load_baggage(self, context: Context | None = None) -> None:
        """
        Load the baggage from the given context.
        """
        trace_id = typing.cast(
            str | None,
            baggage.get_baggage(TRACE_ID_BAGGAGE_KEY, context=context),
        )
        if trace_id:
            # value present in received baggage, so we already propagated values before,
            # keep that as correlation id, then use the current request id
            request_id = self._get_current_request_id()
        else:
            # value not present in received baggage, we've propagated no values yet,
            # this is the first entry point, use trace id as correlation and request id
            trace_id = request_id = self.get_trace_id()

        # causation taken from baggage if present, otherwise current request id itself
        causation_request_id = (
            typing.cast(
                str | None,
                baggage.get_baggage(CAUSATION_REQ_ID_BAGGAGE_KEY, context=context),
            )
            or request_id
        )

        self._set_current_tracing_values(
            request_id=request_id,
            trace_id=trace_id,
            causation_request_id=causation_request_id,
        )

        # set new values in the baggage context for other distributed systems to use
        attach(baggage.set_baggage(TRACE_ID_BAGGAGE_KEY, trace_id))
        attach(baggage.set_baggage(CAUSATION_REQ_ID_BAGGAGE_KEY, request_id))

    def tracing_extras_for_logging(self) -> collections.abc.Mapping[str, typing.Any]:
        """
        Return a dictionary with all the tracing values as a read-only mapping.
        """
        # return Mapping to expose a read-only dictionary that contains up-to-date data
        try:
            stored_values = _tracing_log_extras_var.get()
        except LookupError:
            logging.exception("Tracing extras accessed before being set")
            stored_values = {}
            _tracing_log_extras_var.set(stored_values)
        return stored_values


class MemoryTracingContext(TracingContext):
    """
    In-memory tracing context.
    """

    def get_trace_processor(self) -> SpanProcessor:
        return SimpleSpanProcessor(
            in_memory_span_exporter.InMemorySpanExporter(),
        )


class ConsoleTracingContext(TracingContext):
    """
    Console tracing context.
    """

    def get_trace_processor(self) -> SpanProcessor:
        return SimpleSpanProcessor(ConsoleSpanExporter())


class GoogleTracingContext(TracingContext):
    """
    Google tracing context.
    """

    def get_resources(self) -> resources.Resource:
        return resources.get_aggregated_resources(
            [
                GoogleCloudResourceDetector(raise_on_error=True)  # type: ignore[no-untyped-call]
            ],
        )

    def get_trace_processor(self) -> SpanProcessor:
        return BatchSpanProcessor(
            CloudTraceSpanExporter()  # type: ignore[no-untyped-call]
        )
