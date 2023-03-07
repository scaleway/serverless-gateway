VERSION := $(shell cat VERSION)

IMAGE_REGISTRY := registry.hub.docker.com
IMAGE_ORG := shillakerscw
IMAGE_NAME := scw-sls-gw
IMAGE_TAG := ${IMAGE_REGISTRY}/${IMAGE_ORG}/${IMAGE_NAME}:${VERSION}

SCW_PROJECT_ID := dummy-project-id
SCW_CONTAINER_REGION := fr-par
SCW_CONTAINER_NAME := scw-sls-gw
SCW_CONTAINER_NAMESPACE := scw-sls-gw-test
SCW_CONTAINER_MIN_SCALE := 1

GW_PROXY_PORT := 8000

.PHONY: test
test:
	pytest tests/unit

.PHONY: test-int
test-int:
	pytest tests/integration

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

.PHONY: create-namespace
create-namespace:
	scw container namespace create name=$(SCW_CONTAINER_NAMESPACE) project-id=${SCW_PROJECT_ID} region=${SCW_CONTAINER_REGION}

.PHONY: create-container
create-container:
	$(eval SCW_CONTAINER_NAMESPACE_ID=$(shell scw container namespace list region=${SCW_CONTAINER_REGION} -o json | jq -r '.[] | select(.name=="$(SCW_CONTAINER_NAMESPACE)") | .id'))
	scw container container create namespace-id=${SCW_CONTAINER_NAMESPACE_ID} name=$(SCW_CONTAINER_NAME) min-scale=${SCW_CONTAINER_MIN_SCALE} port=${GW_PROXY_PORT} registry-image=${IMAGE_TAG} region=${SCW_CONTAINER_REGION}

.PHONY: test-int-container
test-int-container:
	$(eval SCW_CONTAINER_ID=$(shell scw container container list region=${SCW_CONTAINER_REGION} -o json | jq -r '.[] | select(.name=="$(SCW_CONTAINER_NAME)") | .id'))
	$(eval  GW_HOST_URL=${shell scw container container get $(SCW_CONTAINER_ID) -o json | jq -r '.domain_name'})
	pytest tests/integration -GW_HOST=$(GW_HOST_URL)