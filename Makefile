VERSION := $(shell cat VERSION)

# TODO - update to use SCW
IMAGE_ORG := shillakerscw
IMAGE_NAME := scw-sls-gw
IMAGE_TAG := ${IMAGE_ORG}/${IMAGE_NAME}:${VERSION}

.PHONY: test
test:
	python -m pytest tests/unit -v

.PHONY: test-int
test-int:
	python -m pytest tests/integration -v

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
	docker build . -t ${IMAGE_TAG}

.PHONY: push-image
push-image:
	docker push ${IMAGE_TAG}
