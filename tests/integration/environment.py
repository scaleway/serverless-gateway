import os
from dataclasses import dataclass

import boto3
import requests


@dataclass
class IntegrationEnvironment:
    gw_url: str

    # The disitinction of those two variables is relevant for docker compose
    # URL of the function visible from our host
    host_func_a_url: str
    # URL of the function visible from the gateway
    gw_func_a_url: str

    # S3 bucket
    s3_bucket: str
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_region: str

    @staticmethod
    def get_docker_compose_env():
        return IntegrationEnvironment(
            gw_url="http://localhost:8080",
            host_func_a_url="http://localhost:8004",
            gw_func_a_url="http://func-a:80",
            s3_bucket="tokens",
            s3_endpoint="http://localhost:9000",
            s3_access_key="minioadmin",
            s3_secret_key="minioadmin",
            s3_region="whatever",
        )

    @staticmethod
    def get_scw_env():
        func_a_url = f'https://{os.environ["FUNC_A_DOMAIN"]}:443'
        return IntegrationEnvironment(
            gw_url=f'https://{os.environ["GATEWAY_HOST"]}:443',
            host_func_a_url=func_a_url,
            gw_func_a_url=func_a_url,
            s3_bucket=os.environ["S3_BUCKET_NAME"],
            s3_endpoint=os.environ["S3_ENDPOINT"],
            s3_access_key=os.environ["SCW_ACCESS_KEY"],
            s3_secret_key=os.environ["SCW_SECRET_KEY"],
            s3_region=os.environ["S3_REGION"],
        )

    @property
    def gw_admin_url(self):
        return self.gw_url + "/scw"

    @property
    def gw_auth_url(self):
        return self.gw_url + "/token"

    def get_auth_session(self) -> requests.Session:
        response = requests.post(self.gw_auth_url)
        response.raise_for_status()

        s3 = boto3.resource(
            "s3",
            region_name=self.s3_region,
            endpoint_url=self.s3_endpoint,
            aws_access_key_id=self.s3_access_key,
            aws_secret_access_key=self.s3_secret_key,
        )

        # It's important to sort the keys by date because
        # the keys are persisted in the bucket after a container reload
        objects = sorted(
            s3.Bucket(self.s3_bucket).objects.all(),
            key=lambda obj: obj.last_modified,
            reverse=True,
        )

        assert objects, "No key was found in bucket!"
        auth_key = objects[0].key

        session = requests.Session()
        session.headers["X-Auth-Token"] = auth_key

        return session
