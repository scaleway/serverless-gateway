VERSION := $(shell cat VERSION)

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

.PHONY: build-image
build-image:
	docker build . -t 'scaleway/scw-sls-gw:${VERSION}'

.PHONY: push-image
push-image:
	docker push 'scaleway/scw-sls-gw:${VERSION}'
