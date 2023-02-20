VERSION := $(shell cat VERSION)

.PHONY: test
test:
	python -m pytest tests/unit

.PHONY: test-int
test-int:
	python -m pytest tests/integration

.PHONY: lint
lint:
	isort . --check-only
	black . --check --diff --color
	flake8
	mypy .

.PHONY: tidy
tidy:
	cd gateway
	black .
	isort .

.PHONY: build-image
build-image:
	docker build . -t 'scaleway/scw-sls-gw:${VERSION}'

.PHONY: push-image
push-image:
	docker push 'scaleway/scw-sls-gw:${VERSION}'
