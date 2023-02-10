.PHONY: test-int
test-int:
	pytest

.PHONY: lint
lint:
	isort . --check-only
	black . --check --diff --color
	flake8
	mypy .

.PHONY: tidy
tidy:
	cd scw-sls-gw
	black .
	isort .

.PHONY: build-docker
build-docker:
	docker build . -t 'scw-sls-gw'
