.PHONY: install run-mock-api demo eval test lint

install:
	pip install -e .[dev]

run-mock-api:
	python -m mock_api.server

demo:
	python -m cli demo happy

eval:
	python -m cli eval

test:
	pytest

