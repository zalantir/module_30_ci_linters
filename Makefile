.PHONY: install fmt lint type test ci

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

fmt:
	black .
	isort .

lint:
	flake8 .
	black --check .
	isort --check-only .

type:
	mypy .

test:
	pytest

ci: lint type test
