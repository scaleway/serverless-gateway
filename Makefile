VERSION := $(shell cat VERSION)

# TODO - update to use SCW
IMAGE_ORG := shillakerscw
IMAGE_NAME := scw-sls-gw
IMAGE_TAG := ${IMAGE_ORG}/${IMAGE_NAME}:${VERSION}

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
	docker build . -t ${IMAGE_TAG}

.PHONY: push-image
push-image:
	docker push ${IMAGE_TAG}
