FROM python:3.10-alpine

# Install NGINX
RUN apk update
RUN apk add nginx=1.22.1-r0

# Set up poetry
RUN pip install -U pip
RUN pip install poetry==1.2.0

# Poetry install (just poetry files to avoid breaking cache)
WORKDIR /scw-gateway
COPY scw-gateway/pyproject.toml .
COPY scw-gateway/poetry.lock .

# Keep Poetry happy with imported module
COPY scw-gateway/scw_gateway/__init__.py scw_gateway/__init__.py

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

WORKDIR /

# Copy in NGINX configs
COPY container/nginx.conf /etc/nginx/nginx.conf
COPY container/conf.d/ /etc/nginx/conf.d/
COPY container/helpers/ /etc/nginx/helpers

# Copy rest of code
COPY scw-gateway/ /scw-gateway/

# Copy startup script
COPY container/startup.sh /startup.sh
CMD ["sh", "/startup.sh"]
