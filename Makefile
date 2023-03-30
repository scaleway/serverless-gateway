VERSION := $(shell cat VERSION)

IMAGE_REGISTRY := registry.hub.docker.com
IMAGE_ORG := scaleway
IMAGE_NAME := serverless-gateway
IMAGE_TAG := ${IMAGE_REGISTRY}/${IMAGE_ORG}/${IMAGE_NAME}:${VERSION}

SCW_CONTAINER_NAMESPACE := scw-sls-gw
SCW_CONTAINER_NAME := scw-sls-gw
SCW_CONTAINER_MIN_SCALE := 1
SCW_CONTAINER_MEMORY_LIMIT := 1024
CONTAINER_CUSTOM_DOMAIN := your-custom-domain-name

# Include s3 configuration
include gateway.env

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

SECRET_ENV_CMD_OPTIONS := secret-environment-variables.0.key=SCW_ACCESS_KEY \
		                  secret-environment-variables.0.value=${SCW_ACCESS_KEY} \
		                  secret-environment-variables.1.key=SCW_SECRET_KEY \
		                  secret-environment-variables.1.value=${SCW_SECRET_KEY} \
		                  secret-environment-variables.2.key=S3_ENDPOINT \
		                  secret-environment-variables.2.value=${S3_ENDPOINT} \
		                  secret-environment-variables.3.key=S3_REGION \
		                  secret-environment-variables.3.value=${S3_REGION} \
		                  secret-environment-variables.4.key=S3_BUCKET_NAME \
		                  secret-environment-variables.4.value=${S3_BUCKET_NAME}

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
	cd gateway
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
# Serverless namespace
#--------------------------
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

#--------------------------
# Container deploy
#--------------------------
.PHONY: create-container
create-container:
	$(eval $(call namespace_id,_id))
	scw container container create \
		namespace-id=${_id} \
		name=$(SCW_CONTAINER_NAME) \
		min-scale=${SCW_CONTAINER_MIN_SCALE} \
		memory-limit=${SCW_CONTAINER_MEMORY_LIMIT} \
		registry-image=${IMAGE_TAG} \
		region=${SCW_API_REGION} \
		${SECRET_ENV_CMD_OPTIONS}

.PHONY: deploy-container
deploy-container:
	$(eval $(call container_id,_id))
	scw container container deploy ${_id} \
	region=${SCW_API_REGION}

.PHONY: add-container-endpoint
add-container-endpoint:
	$(eval $(call container_id,_id))
	scw container domain create \
		container_id=${_id} \
		hostname=${CONTAINER_CUSTOM_DOMAIN}

#--------------------------
# Container update
#--------------------------
.PHONY: update-container
update-container:
	$(eval $(call container_id,_id))
	scw container container update ${_id} \
		min-scale=${SCW_CONTAINER_MIN_SCALE} \
		memory-limit=${SCW_CONTAINER_MEMORY_LIMIT} \
		registry-image=${IMAGE_TAG} \
		region=${SCW_API_REGION} \
		${SECRET_ENV_CMD_OPTIONS}

.PHONY: update-container-without-deploy
update-container-without-deploy:
	$(eval $(call container_id,_id))
	scw container container update ${_id} \
		min-scale=${SCW_CONTAINER_MIN_SCALE} \
		memory-limit=${SCW_CONTAINER_MEMORY_LIMIT} \
		registry-image=${IMAGE_TAG} \
		region=${SCW_API_REGION} \
		redeploy=false \
		${SECRET_ENV_CMD_OPTIONS}


#--------------------------
# Container check
#--------------------------
.PHONY: check-container
check-container:
	$(eval $(call container_id,_id))
	scw container container get ${_id} \
	region=${SCW_API_REGION}

#--------------------------
# S3
#--------------------------
.PHONY: set-up-s3-cli
set-up-s3-cli:
	scw object config install type=s3cmd

.PHONY: create-s3-bucket
create-s3-bucket:
	s3cmd mb s3://${S3_BUCKET_NAME}

#--------------------------
# Cleanup
#--------------------------
.PHONY: delete-container
delete-container:
	$(eval $(call container_id,_id))
	scw container container delete ${_id} \
	region=${SCW_API_REGION}

.PHONY: delete-namespace
delete-namespace:
	$(eval $(call namespace_id,_id))
	scw container namespace delete ${_id} \
	region=${SCW_API_REGION}

.PHONY: delete-bucket
delete-bucket:
	s3cmd rb s3://${S3_BUCKET_NAME}

#--------------------------
# Tokens
#--------------------------
.PHONY: list-tokens
list-tokens:
	@s3cmd ls s3://${S3_BUCKET_NAME} | awk -F'/' '{print$$4}'

#--------------------------
# Tests
#--------------------------
.PHONY: test
test:
	pytest tests/unit

.PHONY: test-int
test-int:
	pytest tests/integration

.PHONY: test-int-container
test-int-container:
	$(eval SCW_CONTAINER_ID=$(shell scw container container list region=${SCW_API_REGION} -o json | jq -r '.[] | select(.name=="$(SCW_CONTAINER_NAME)") | .id'))
	$(eval  GW_HOST_URL=${shell scw container container get $(SCW_CONTAINER_ID) region=${SCW_API_REGION} -o json | jq -r '.domain_name'})
	pytest tests/integration -GW_HOST=$(GW_HOST_URL)
