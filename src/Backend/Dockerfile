FROM python:3.11-slim as builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VERSION=2.0.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    PATH="/opt/poetry/bin:$PATH"

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install --no-install-recommends -y \
        curl build-essential git
RUN curl -sSL https://install.python-poetry.org | python -

WORKDIR /app
COPY . ./
RUN poetry self add poetry-plugin-export==1.8.0
RUN poetry add ddtrace
RUN poetry lock
RUN poetry install --only build

RUN mkdir build

RUN make build

FROM python:3.11-slim-bookworm

WORKDIR /app

COPY --from=builder /app/dist/stt.pex ./
COPY --from=builder /app/alembic.ini ./
COPY --from=builder /app/migrations/ ./migrations

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get -y upgrade && \
    apt-get install --no-install-recommends -y \
    ffmpeg \
    espeak && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip uninstall -y pip

ENV PORT=8080 \
    GUNICORN_WORKERS=6 \
    VERSION=$VERSION

CMD exec python stt.pex --bind :$PORT --workers $GUNICORN_WORKERS --threads 1 --timeout 0 --worker-tmp-dir=/dev/shm