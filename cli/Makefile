IMAGE_REGISTRY := docker.io
IMAGE_ORG := scaleway
IMAGE_NAME := serverless-gateway
IMAGE_TAG := ${IMAGE_REGISTRY}/${IMAGE_ORG}/${IMAGE_NAME}:0.0.0

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

#-------------------------
# Container image
#-------------------------

.PHONY: build-image
build-image:
	docker build . -t ${IMAGE_TAG}

.PHONY: push-image
push-image:
	docker push ${IMAGE_TAG}

#--------------------------
# Tests
#--------------------------

FIXTURES_NAMESPACE_NAME := function-fixtures

define fixture_namespace_id
	ns_id=$(shell scw function namespace \
		  list name=${FIXTURES_NAMESPACE_NAME} -o json | \
		  jq -r '.[0] | .id')
	$(1) := $$(ns_id)
endef

define fixture_host
	$(eval $(call fixture_namespace_id,_id))
	fnc_host := $(shell scw function function \
		  list namespace-id=${_id} -o json | \
		  jq -r '.[] | select(.name==$(1)) | .domain_name')
	$(2) := $$(fnc_host)
endef

.PHONY: test
test:
	pytest tests/unit

.PHONY: test-int
test-int:
	pytest tests/integration

.PHONY: deploy-function-fixtures
deploy-function-fixtures:
	cd endpoints && serverless deploy

.PHONY:
get-func-a-host:
	$(eval $(call fixture_host,"func-a",_func_a_host))
	echo ${_func_a_host}
