.PHONY: test
test:
	poetry run pytest

.PHONY: lint
lint:
	poetry run isort . --check-only
	poetry run black . --check --diff --color
	poetry run flake8
	poetry run mypy .

.PHONY: tidy
tidy:
	poetry run black .
	poetry run isort .

