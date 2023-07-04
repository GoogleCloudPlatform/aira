SHELL=/bin/bash

setup:
	poetry install --sync

fixture:
	poetry run python fixture.py

format:
	poetry run shed --py310-plus --refactor $(shell find src tests -type f -iname '*.py' | xargs)
	poetry run isort --atomic $(shell find src tests -type f -iname '*.py' | xargs)

lint:
	poetry lock --check
	poetry run pylint --rcfile=pylint.toml src tests
	poetry run mypy --config-file=mypy.ini src tests

test:
	poetry run pytest -vvv \
	--mypy --mypy-config-file=mypy.ini \
	--pylint --pylint-rcfile=pylint.toml \
	--cov=api --cov-report=term-missing \
	src tests

server:
	poetry run uvicorn --host=0.0.0.0 --port 8080 --reload --reload-dir=src main:app

migrate:
	poetry run alembic upgrade head

.PHONY: setup format lint test server migrate
