#-------------------------
# Format
#-------------------------

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

#--------------------------
# Tests
#--------------------------

.PHONY: test
test:
	poetry run pytest tests/unit

.PHONY: test-int
test-int:
	poetry run pytest -m "not deployed" tests/integration

.PHONY: test-int-deployed
test-int-deployed:
	poetry run pytest tests/integration
