VERSION := $(shell cat VERSION)

IMAGE_REGISTRY := registry.hub.docker.com
IMAGE_ORG := shillakerscw
IMAGE_NAME := scw-sls-gw
IMAGE_TAG := ${IMAGE_REGISTRY}/${IMAGE_ORG}/${IMAGE_NAME}:${VERSION}

SCW_CONTAINER_NAMESPACE := scw-sls-gw
SCW_CONTAINER_NAME := scw-sls-gw
SCW_CONTAINER_MIN_SCALE := 1

CONTAINER_CUSTOM_DOMAIN := your-custom-domain-name

# Set SCW_API_REGION to fr-par if the env var SCW_API_REGION is not already set
SCW_API_REGION ?= fr-par

# Function to get the container ID
define container_id
	ns_id=$(shell scw container container \
		  list region=${SCW_API_REGION} -o json | \
		  jq -r '.[] | select(.name=="$(SCW_CONTAINER_NAME)") | .id')

	$(1) := $$(ns_id)
endef

# Function to get the namespace ID
define namespace_id
	ns_id=$(shell scw container namespace \
		  list region=${SCW_API_REGION} -o json | \
		  jq -r '.[] | select(.name=="$(SCW_CONTAINER_NAMESPACE)") | .id')
	$(1) := $$(ns_id)
endef

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
	scw container namespace \
		create \
		name=$(SCW_CONTAINER_NAMESPACE) \
		region=${SCW_API_REGION}

.PHONY: check-namespace
check-namespace:
	$(eval $(call namespace_id,_id))
	scw container namespace get ${_id} \
	region=${SCW_API_REGION}

.PHONY: create-container
create-container:
	$(eval $(call namespace_id,_id))
	scw container container create \
		namespace-id=${_id} \
		name=$(SCW_CONTAINER_NAME) \
		min-scale=${SCW_CONTAINER_MIN_SCALE} \
		registry-image=${IMAGE_TAG} \
		region=${SCW_API_REGION}

.PHONY: deploy-container
deploy-container:
	$(eval $(call container_id,_id))
	scw container container deploy ${_id} \
	region=${SCW_API_REGION}

.PHONY: update-container
update-container:
	$(eval $(call container_id,_id))
	scw container container update ${_id} \
		min-scale=${SCW_CONTAINER_MIN_SCALE} \
		registry-image=${IMAGE_TAG} \
		region=${SCW_API_REGION}

.PHONY: check-container
check-container:
	$(eval $(call container_id,_id))
	scw container container get ${_id} \
	region=${SCW_API_REGION}

.PHONY: add-container-endpoint
add-container-endpoint:
	$(eval $(call container_id,_id))
	scw container domain create \
		container_id=${_id} \
		hostname=${CONTAINER_CUSTOM_DOMAIN}

.PHONY: test-int-container
test-int-container:
	$(eval SCW_CONTAINER_ID=$(shell scw container container list region=${SCW_API_REGION} -o json | jq -r '.[] | select(.name=="$(SCW_CONTAINER_NAME)") | .id'))
	$(eval  GW_HOST_URL=${shell scw container container get $(SCW_CONTAINER_ID) region=${SCW_API_REGION} -o json | jq -r '.domain_name'})
	pytest tests/integration -GW_HOST=$(GW_HOST_URL)
