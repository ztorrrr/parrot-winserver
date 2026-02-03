"""
AWS Secret Manager 유틸리티
"""

import base64
import json

import boto3
from botocore.exceptions import ClientError
from cachetools.func import ttl_cache
from excel_tool.common.config.constant import DEFAULT_REGION


class NotFoundSecretKeyError(Exception):
    def __init__(self, key):
        Exception.__init__(
            self, f"'Secrets Manager can't find the specified secret : {key}"
        )


class NotFoundSecretItemError(Exception):
    def __init__(self, key, item):
        Exception.__init__(self, f"Secrets can't find the specified item : {item}")


@ttl_cache()
def get_secret(secret_name, region_name=DEFAULT_REGION):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=str(secret_name))
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            raise NotFoundSecretKeyError(secret_name)
        raise
    else:
        if "SecretString" in response:
            secret = response["SecretString"]
        else:
            secret = base64.b64decode(response["SecretBinary"])

        return json.loads(secret)
