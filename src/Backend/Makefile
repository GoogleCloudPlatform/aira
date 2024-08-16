SHELL=/bin/bash

build:
	mkdir -p dist
	poetry build --format=wheel
	poetry export --without-hashes | sed 's/ @ file:.* ; / ; /' > dist/requirements.txt
	poetry run pex \
		--compile \
		--no-compress \
		--strip-pex-env \
		--find-links=dist \
		--script="uvicorn" \
		--sources-directory=src \
		--output-file=dist/stt.pex \
		--inject-arg="api.asgi:app" \
		--inject-env="_GIT_SHA=$(shell git rev-parse HEAD)" \
		--requirement=dist/requirements.txt
	rm dist/*.whl

setup:
	poetry install --sync

fixture:
	poetry run python fixture.py

format:
	poetry run ruff format src tests
	poetry run ruff check src tests --fix

lint:
	poetry check --lock
	poetry run ruff check src tests
	poetry run mypy --config-file=mypy.ini src tests

test:
	SQLALCHEMY_WARN_20=1 poetry run pytest -vvv \
	--cov=api --cov-report=term-missing \
	src tests

server:
	poetry run uvicorn --host=0.0.0.0 --port 8080 --reload --reload-dir=src api.asgi:app

migrate:
	poetry run alembic upgrade head

.PHONY: build setup format lint test server migrate