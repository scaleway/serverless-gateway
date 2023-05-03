#-------------------------
# Format
#-------------------------

.PHONY: lint
lint:
	isort . --check-only
	black . --check --diff --color
	flake8
	mypy .

.PHONY: tidy
tidy:
	black .
	isort .

#--------------------------
# Tests
#--------------------------

.PHONY: test
test:
	pytest tests/unit

.PHONY: test-int
test-int:
	pytest tests/integration

