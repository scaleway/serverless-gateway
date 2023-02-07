# Scaleway Serverless API Gateway

This is a self-hosted gateway for use in building larger serverless applications.

## Setup

Run

```
docker compose build
docker compose up
```

Then in a separate terminal

```
curl http://localhost:8080

curl http://localhost:8080/scw/ping
```

