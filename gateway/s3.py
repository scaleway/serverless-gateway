import os

import boto3
from botocore.exceptions import ClientError
from loguru import logger


class Bucket(object):
    """
    Manage Scaleway s3 bucket
    """

    def __init__(self):
        self._scw_access_key = os.environ.get("SCW_ACCESS_KEY")
        self._scw_secret_key = os.environ.get("SCW_SECRET_KEY")
        self._scw_s3_region = os.environ.get("S3_REGION")
        self._scw_s3_endpoint = os.environ.get("S3_ENDPOINT")
        self._scw_s3_bucket = os.environ.get("S3_BUCKET_NAME")

    def _connect(self):
        """
        Connect to Scaleway s3 bucket
        """
        return boto3.resource(
            "s3",
            region_name=self._scw_s3_region,
            endpoint_url=self._scw_s3_endpoint,
            aws_access_key_id=self._scw_access_key,
            aws_secret_access_key=self._scw_secret_key,
        )

    def upload(self, data: str) -> bool:
        """
        Upload data to s3 bucket
        """
        try:
            client = self._connect()
            obj = client.Object(self._scw_s3_bucket, data)
            obj.put(Body=bytes(data, "utf-8"))

        except ClientError as e:
            logger.info(f"error while uploading data to s3 bucket: {e}")
            return False

        return True
